# FIBSEM_Maestro

Software for (cryo/RT) volume-EM acquisition. It allows to acquire the big volume in constant high quality.  

Key features:
- Usage of deep learning model for segmentation of region of interest. The segmented region is used for:
  - Resolution calculation ([siFRC](https://github.com/prabhatkc/siFRC) or others)
  - Autofocusing, autostigmator, auto-lens alignment (multiple criterions and sweeping strategies)
  - Drift correction & FoV optimization (template matching, or segmented region centering)
  - Auto contrast-brightness (whole image or segmented region)
- Email attention
- Works with ThermoFisher Autoscript. Support of [OpenFIBSEM](https://github.com/DeMarcoLab/fibsem) for other vendors (Tescan, Zeiss) is planned.

Drift correction with segmentation aid


https://github.com/user-attachments/assets/45ff2652-db7e-494b-bb37-505d80c9be56


FoV optimization with segmentation aid


https://github.com/user-attachments/assets/0c56cf67-b3c6-4034-a15c-69c574f1049c

# Step-by-Step Manual (Resin Sample, Non-extended Resolution)

1. **Find the coincidence position**  
   - ROI should be visible in both electron and ion images.

2. **Adjust image conditions**  
   - Tune imaging parameters in both electron and ion imaging. Use highest possible resolution and magnification in FIB.

3. **FIB Tab**  
   - Click `Get Image`.

4. **Set Fiducial**  
   - Select a fiducial and click `Set Fiducial`.  
   - Make sure the selection rectangle handles are inside the rectangle.

5. **Set Acquisition Area (FIB)**  
   - Select the acquisition area and click `Set Acquisition`.  
   - The milling direction is indicated by a small rectangle near the milling edge.

6. **Set Slice Parameters**  
   - Set `Slice Distance`, `Milling Depth`, and `Finding Area`.
   - `Finding Area` defines the area for searching for fiducial.
   - Ensure the finding area around the fiducial does not extend outside the image.

7. **Set Rescan**  
   - Adjust the rescan frequency according to your system's drift behavior (recommended: 1–10).

8. **Save Settings**  
   - Go to `File → Save Settings`.

<img width="1263" height="970" alt="Capture_FIB_arrows" src="https://github.com/user-attachments/assets/5740b99d-b498-4953-ae40-b5d5212fc62e" />

9. **SEM Tab**  
   - Click `Get Image`.

10. **Set Acquisition Area (SEM)**  
    - Select the acquisition area and click `Set Acquisition`.
    - Click to `Align along sample surface`

11. **Adjust Imaging Conditions**  
    - Set `dwell`, `bit depth` and `line integration`.
    - Set `Criterion border` and `tile size`. The border helps to speed up the criterion calculation because it omits the calculation on edge areas.

12. **Save Settings**  
    - Go to `File → Save Settings`.

<img width="1265" height="968" alt="CaptureSEM_arroes" src="https://github.com/user-attachments/assets/216e12f2-ed94-43ca-841c-f6c7f5f2b24d" />


13. **Drift Correction**  
    - Set imaging parameters `Dwell` and `horizontal_field_with` for clear block-face visibility.
    - Click to `Update image`.
    - Click `Remove areas` and set a new fiducial areas in the image. Recomended place is on the corners of block-face.

14. **Set Fiducials for Drift Correction**  
    - Click `Set drift correction area` after each area placement.
    - Click `Update areas`.

15. **Save Settings**  
    - Go to `File → Save Settings`.
      
<img width="1263" height="978" alt="CaptureDC_arrows" src="https://github.com/user-attachments/assets/7ee1e693-d1cd-4e02-a4fc-035537bac122" />


16. **Auto Functions Tab**
    - Go backt to SEM tab and click to `Test imaging` for image update.
    - Ensure all autofunctions have `Slice Number` and `Slice Resolution` zeroed.

18. **Recommended Autofunctions**  
    - **Source Tilt - TFS:** Optimization by manufacturer routine. Run every 200 slices. Test with `Test` button.  
    - **Lens Align - TFS:** Beam centering optimization. Run every 100 slices. Select the area and click `Set AF Area`. For sensitive samples, use `delta_X` parameter and update SEM image manually. Test with `Test` button.  
    - **Stigmation - TFS:** Astigmatism optimization. Run every 50 slices. Select the area and click `Set AF Area`. For sensitive samples, use `delta_X` parameter and update SEM image manually. Test with `Test` button.  
    - **Focus:** Run every 25 slices or set resolution threshold. Select the area and click `Set AF Area`. For sensitive samples, use `delta_X` parameter and update SEM image manually. Test with `Test` button.
    - Set `Dwell` for all used autofunctions.

19. `Run` and enjoy
20. After a few slices, check the calculated resolution in the console or log. Then, set `resolution_threshold` in SEM image (stop if the calculated resoluton crosses this limir) or set the threshold to `executed_resolution`. Set email attention if needed.
    
<img width="1271" height="975" alt="CaptureAF_arrows" src="https://github.com/user-attachments/assets/73bb46d5-c3ed-473c-853e-c947b8ed289c" />

# Recommendations for Cryo

- Use manufacturer routines only on the GIS layer outside of exposed areas.  
- Set `Rescan` to 1.  
- For focusing autofunction, use `Line Focus`. Set `Regions` and `Keep Time` so all regions fit into the selected area. The signal should overflow. Test with `Test` button.
...Cryo workflow will be introduced soon...
