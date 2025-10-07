# Modular structure


BlendArMocap is split into separate modules: 
- mediapipe
- freemocap
- transfer
- socket (to be implemented)<br>

The modules have their own registration functions which gets called by `cgt_registration`.
To add new tabs in the BlendAR UI-Panel use the `parent_id: 'UI_PT_CGT_Panel'`. 
In case you need to add new entries to the add-ons preferences, add the 
draw function to `cgt_core.cgt_interface.cgt_core_panel.addon_prefs`.<br>

While all modules may access the core, try to keep modules as standalone as possible. 
You may access other modules by using their public operators. Ensure to not weave code around other modules.

If installation fails (mainly import's versions are uncompatable, change cgt_dependencies.py).

If you are running the addon off your machine and want to see the output while running, uncomment line `# cv2.imshow(self.title, f)` in `cv_stream.py`