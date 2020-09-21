from astropy.io import fits
from astropy import wcs
import argparse
import os
import shutil
import subprocess
import sys
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


class DownloadFieldsError(Exception): pass

class SextractorError(Exception): pass


def download_fields(RA, DEC, out_path):
    """Attempts to download the 5 waveband field images to out_path.  Returns the
       fields downloaded as fits objects."""
    print 'Downloading', out_path.split('/')[-1]
    proc = subprocess.Popen(['./downloadFields.sh', RA, DEC, out_path], stdout = subprocess.PIPE, universal_newlines = True)
    proc.stdout.close()
    res = proc.wait()
    if res != 0: raise DownloadFieldsError

    fields = [] 
    # return fields as astropy objects
    for f in sorted(os.listdir(out_path)):
        fields.append(fits.open(os.path.join(out_path, f), ignore_missing_end = True))
    print 'Finished downloading {} field images.'.format(len(fields))
    return fields


def save_crop_fits(f, refx, refy, size, path, ra, dec):
    """Crops the image to size x size, with (refx, refy)
       being the cetner of the galaxy."""
    
    # check to see if size / 2 pixels are available in all directions
    # i.e. not near the edge of the image
    size = int(size / 2)
    if refx - size < 0: 
        size = refx
    if refx + size > f[0].data.shape[1] - 1:
        size = f[0].data.shape[1] - 1 - refx
    if refy - size < 0:
        size = refy
    if refy + size > f[0].data.shape[0] - 1:
        size = f[0].data.shape[0] - 1 - refy

    xmin, xmax = refx - size, refx + size
    ymin, ymax = refy - size, refy + size
    
    # create cropped fits
    nf = fits.PrimaryHDU()
    nf.data = f[0].data[ymin : ymax, xmin : xmax]
    nf.header = f[0].header
    
    # update the reference pixel information to be the center of the galaxy
    nf.header['CRPIX1'] = size
    nf.header['CRPIX2'] = size
    nf.header['CRVAL1'] = float(ra)
    nf.header['CRVAL2'] = float(dec)
    # save the file to specified path
    fits.HDUList([nf]).writeto(path, overwrite = True)
    return nf.data.shape, size * 2


def get_num_stars(path, prob):
    """Runs the sextactor on the fits image and counts the number
       of stars that have a class probability of prob."""     
    f = None 
    try:
        proc = subprocess.Popen(['sex', path, '-CATALOG_NAME', 'star_out.txt'], stderr = subprocess.PIPE)
        out, err = proc.communicate()
        res = proc.wait()
        if res != 0: raise Exception
        
        count = 0 
        f = open('star_out.txt', 'r')
        for line in f.readlines()[4:]:
            values = ' '.join(line.rstrip().split()).split()
            # only load in the points that are likely to be stars
            if float(values[3]) >= prob: count += 1 

        print '{} stars found in the image'.format(count) 
        return count
    
    except:
        raise SextractorError
    
    finally:
        if f is not None:
            f.close()
            os.remove('star_out.txt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('RA')
    parser.add_argument('DEC')
    parser.add_argument('name', help = 'The name (id) of the galaxy')
    parser.add_argument('-out_dir', default = None, help = 'If set then the images will be saved to outdir/name')
    parser.add_argument('-overwrite', default = 'True', choices = ['True', 'true', '1', 'False', 'false', '0'], help = 'If true then if any galaxies with the same name will be overwritten')
    parser.add_argument('-min_num_stars', default = 10, type = int, help = 'The minimum number of stars needed in at least one waveband image.')
    parser.add_argument('-star_class_prob', default = 0.7, type = float, help = 'The minimum probablity that an object detected counts as a star, should be in range [0, 1].  A galaxy will require min_num_stars at this probability.')
    args = parser.parse_args()

    out_path = args.name
    
    # check that star arguments are valid
    if args.min_num_stars < 0:
        print 'min_num_stars must be >= 0'
        exit(1)

    if args.star_class_prob > 1 or args.star_class_prob < 0:
        print 'star_class_prob must be in range [0, 1]'
        exit(1)

    # check that out_dir exists
    if args.out_dir is not None:
        if not os.path.exists(args.out_dir):
            print args.out_dir, 'is not a valid directory.'
            exit(1)
        else:
            out_path = os.path.join(args.out_dir, args.name)

    # create the output directory
    if os.path.exists(out_path):
        if args.overwrite in ('True', 'true', '1'):
            shutil.rmtree(out_path)
        else:
            print out_path, 'already exists and will not be overwritten'
            exit(1)
    
    os.mkdir(out_path)
    
    fields = None
    try:
        fields = download_fields(args.RA, args.DEC, out_path)
    
        # X Ref - CRPIX1
        # Y Ref - CRPIX2
        # X Ref Ra - CRVAL1
        # Y Ref Dec - CRVAL2
        # Ra deg per col pixel - CD1_1
        # Ra deg per row pixel - CD1_2
        # Dec deg per col pixel - CD2_1
        # Dec deg per row pixel - CD2_2
        color_names = ('g', 'i', 'r', 'u', 'z')
        crop_size = 100
        # store the center pixels in case of re-copping
        gal_centers = []
        result_crops = []
        for i in range(5):
            center_x = int(fields[i][0].header['CRPIX1'] - ((fields[i][0].header['CRVAL2'] - float(args.DEC)) / fields[i][0].header['CD2_1']))
            center_y = int(fields[i][0].header['CRPIX2'] - ((fields[i][0].header['CRVAL1'] - float(args.RA)) / fields[i][0].header['CD1_2'])) 
            gal_centers.append((center_x, center_y))
            path = '{}/{}.fits'.format(out_path, color_names[i])
            
            # if the first waveband, figure out what zoom level it needs ot be at
            if i == 0:
                num_stars = 0
                while num_stars < args.min_num_stars:
                    crop_size *= 1.1
                    print 'Running sextractor on image size of', crop_size
                    res, size_used = save_crop_fits(fields[i], center_x, center_y, crop_size, path, args.RA, args.DEC)
                    num_stars = get_num_stars(path, args.star_class_prob)
                    # once the image can no longer get bigger
                    if size_used < int(crop_size / 2) * 2: 
                        break
                result_crops.append(res)
            # otherwize assume the crop_size has been found and just crop the image
            else:
                result_crops.append(save_crop_fits(fields[i], center_x, center_y, crop_size, path, args.RA, args.DEC)[0])

        # check that all the crops are the same size, if they arent then make them the same (chose smallest one)
        for i in range(len(result_crops) - 1):
            # if difference is found the find the smallest x and y crop
            if result_crops[i] != result_crops[i+1]: 
                smin = 10000
                for c in result_crops: smin = min(smin, c[0], c[1])

                print 'Recropping images to size', smin
                for f in os.listdir(out_path):  os.remove('{}/{}'.format(out_path, f))
                for i in range(5):
                    save_crop_fits(fields[i], gal_centers[i][0], gal_centers[i][1], smin, '{}/{}.fits'.format(out_path, color_names[i]), args.RA, args.DEC)
                
                break
               
    except Exception, e:
        if fields is not None: 
            for f in fields: f.close()
        raise e

    finally:
        # clean up frame files
        for f in os.listdir(out_path):
            if 'frame' in f:
                try: os.remove(os.path.join(out_path, f))
                except: pass
       
        if len([p for p in os.listdir(out_path) if '.fits' in p]) < 2:
            print 'There was an error and no wavebands could be used, removing the directory\n\n'
            shutil.rmtree(out_path)

        # if core sumps were generated, remove them
        for f in os.listdir('.'):
            if 'core' in f:
                try: os.remove(f)
                except: pass
                    




        



