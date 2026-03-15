(
    SELECTING_LANGUAGE,     # 0  — first-run language selection
    MAIN_MENU,              # 1  — welcome screen
    SELECTING_SPECIES,      # 2  — step 1
    SELECTING_OBS_TYPE,     # 3  — step 2
    UPLOADING_PHOTOS,       # 4  — step 3
    ENTERING_DATE,          # 5  — step 4
    SELECTING_LOCATION_METHOD,  # 6  — step 5 method picker
    AWAITING_LOCATION,      # 7  — step 5 receiving geo OR text coords
    ENTERING_LOCATION_NAME, # 8  — step 6
    ENTERING_OBSERVER_NAME, # 9  — step 7
    ENTERING_NOTES,         # 10 — step 8
    CONFIRMATION,           # 11 — review & send
    EDITING_FIELD,          # 12 — edit field picker
) = range(13)
