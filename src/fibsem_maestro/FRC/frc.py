import fibsem_maestro.FRC.frc_utils as frc_util
import fibsem_maestro.FRC.secondary_utils as su
import numpy as np
import matplotlib.pyplot as plt

def frc(img, pixel_size, show_image=False):
    threshold = 'EM'
    inside_square	= True
    anaRing			= True
    info_split     = True
    img = img.astype(np.float32)
    img = su.normalize_data_ab(0, 1, img)
    sa1, sa2, sb1, sb2 = frc_util.diagonal_split(img)
    sa1 = frc_util.apply_hanning_2d(su.normalize_data_ab(0, 1, sa1))
    sa2 = frc_util.apply_hanning_2d(su.normalize_data_ab(0, 1, sa2))
    #sb1 = frc_util.apply_hanning_2d(su.normalize_data_ab(0, 1, sb1))
    #sb2 = frc_util.apply_hanning_2d(su.normalize_data_ab(0, 1, sb2))
    xc, corr1, xt, thres_val = frc_util.FRC(sa1, sa2, thresholding=threshold, inscribed_rings=inside_square, analytical_arc_based=anaRing, info_split=info_split)
    #_, corr2, _, _           = frc_util.FRC(sb1, sb2, thresholding=threshold, inscribed_rings=inside_square, analytical_arc_based=anaRing, info_split=info_split)
    #_, corr3, _, _           = frc_util.FRC(sa1, sb1, thresholding=threshold, inscribed_rings=inside_square, analytical_arc_based=anaRing, info_split=info_split)
    #_, corr4, _, _           = frc_util.FRC(sa2, sb1, thresholding=threshold, inscribed_rings=inside_square, analytical_arc_based=anaRing)
    #_, corr5, _, _          = frc_util.FRC(sa2, sb2, thresholding=threshold, inscribed_rings=inside_square, analytical_arc_based=anaRing)
    #_, corr6, _ , _         = frc_util.FRC(sb1, sb2, thresholding=threshold, inscribed_rings=inside_square, analytical_arc_based=anaRing)
    #corr_avg                 = (corr1+corr2+corr3)/3.0
    corr_avg 				= corr1
        
    if show_image:
        plt.plot(xc[:-1]/2, corr_avg[:-1], label = 'chip-FRC', color='black')
        plt.plot(xt[:-1]/2, (thres_val[3])[:-1], label='EM', color='Orange')
        plt.xlim(0.0, 0.5)
        plt.ylim(0.0, 1)
        plt.grid(linestyle='dotted', color='black', alpha=0.3) 
        plt.xticks(np.arange(0.0, 0.5, step=0.03))
        plt.yticks(np.arange(0, 1, step=0.1))
        plt.legend(prop={'size':13})
        plt.xlabel('Spatial Frequency (unit$^{-1}$)', {'size':13})
        # plt.title ('Fourier Ring Correlation (FRC)', {'size':20})
        plt.tick_params(axis='both', labelsize=7)
    	
    cross_i = next(x for x, val in enumerate(corr_avg) if val < thres_val[3][0])# EM cros
    freq = xc[cross_i] / 2
    resolution = (1/freq)*pixel_size*np.sqrt(2)
    #print(f'Resolution: {resolution}')
    return resolution
