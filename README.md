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

# Step-by-Step Manual (Resin Samples)

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
   - Ensure the finding area around the fiducial does not extend outside the image.

7. **Set Rescan**  
   - Adjust the rescan frequency according to your system's drift behavior (recommended: 1–10).

8. **Save Settings**  
   - Go to `File → Save Settings`.

9. **SEM Tab**  
   - Click `Get Image`.

10. **Set Acquisition Area (SEM)**  
    - Select the acquisition area and click `Set Acquisition`.

11. **Adjust Imaging Conditions**  
    - Set `Pixel Size` and other imaging parameters as needed.

12. **Save Settings**  
    - Go to `File → Save Settings`.

13. **Drift Correction**  
    - Set `Correction Area` (should be larger than allowed by the hardware).  
    - Click `Apply Settings` and `Clear Drift Corr`.

14. **Set Fiducials for Drift Correction**  
    - Set one or more fiducials in the image and click `Set Areas`.

15. **Save Settings**  
    - Go to `File → Save Settings`.

16. **Auto Functions Tab**  
    - Ensure all autofunctions have `Slice Number` and `Slice Resolution` zeroed.

17. **Recommended Autofunctions**  
    - **Source Tilt - TFS:** Optimization by manufacturer routine. Run every 200 slices. Test with `Test` button.  
    - **Lens Align - TFS:** Beam centering optimization. Run every 100 slices. Select the area and click `Set AF Area`. For sensitive samples, use `ShiftX` parameter and update SEM image manually. Test with `Test` button.  
    - **Stigmation - TFS:** Astigmatism optimization. Run every 50 slices. Select the area and click `Set AF Area`. For sensitive samples, use `ShiftX` parameter and update SEM image manually. Test with `Test` button.  
    - **Focus:** Run every 25 slices or set resolution threshold. Select the area and click `Set AF Area`. For sensitive samples, use `ShiftX` parameter and update SEM image manually. Test with `Test` button.

18. `Run` and enjoy

# Recommendations for Cryo

- Use manufacturer routines only on the GIS layer outside of exposed areas.  
- Set `Rescan` to 1.  
- For focusing autofunction, use `Line Focus`. Set `Regions` and `Keep Time` so all regions fit into the selected area. The signal should overflow. Test with `Test` button.
