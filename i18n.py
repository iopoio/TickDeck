"""
i18n.py — Internationalization dictionaries for TickDeck app page (index.html)
Korean (T_KO) and English (T_EN) translations for all user-facing text.
"""

T_KO = {
    # ── meta ──
    "meta_title": "TickDeck \u2014 \ub2f9\uc2e0\uc758 \uc6f9\uc0ac\uc774\ud2b8\ub97c PPT\ub85c",
    "meta_desc": "URL\ub9cc \uc785\ub825\ud558\uba74 AI\uac00 \ube0c\ub79c\ub4dc \ub9de\ucda4\ud615 \ud504\ub808\uc820\ud14c\uc774\uc158\uc744 \uc790\ub3d9\uc73c\ub85c \ub9cc\ub4e4\uc5b4\ub4dc\ub9bd\ub2c8\ub2e4.",
    "meta_canonical": "https://tickdeck.site/app",
    "meta_og_title": "TickDeck \u2014 AI PPT \uc0dd\uc131\uae30",
    "meta_og_desc": "URL \ud558\ub098\uba74 \ube0c\ub79c\ub4dc \ub9de\ucda4\ud615 \ud504\ub808\uc820\ud14c\uc774\uc158\uc774 5\ubd84 \uc774\ub0b4\uc5d0 \uc644\uc131\ub429\ub2c8\ub2e4.",
    "meta_og_url": "https://tickdeck.site/app",

    # ── nav ──
    "nav_home_href": "/",
    "nav_lang_href": "/en/app",
    "nav_lang_label": "\ud83c\udf10 EN",
    "nav_tokens_suffix": "\uac1c",
    "nav_history_btn": "\uc774\ub825",
    "nav_logout_btn": "\ub85c\uadf8\uc544\uc6c3",

    # ── history modal ──
    "modal_history_title": "\uc0dd\uc131 \uc774\ub825",
    "modal_history_desc": "\uc9c1\uc804 \uc0dd\uc131\uc758 PDF\ub9cc \ubcf4\uad00\ub429\ub2c8\ub2e4 \u00b7 \uc0c8\ub85c \uc0dd\uc131\ud558\uba74 \uc774\uc804 PDF\ub294 \uc0ad\uc81c\ub429\ub2c8\ub2e4",

    # ── survey modal ──
    "survey_title": "\ud83d\udccb TickDeck \uc124\ubb38",
    "survey_desc": "2~3\ubd84\uc774\uba74 \ub05d\ub098\ub294 \uac04\ub2e8\ud55c \uc124\ubb38\uc785\ub2c8\ub2e4. \uc644\ub8cc \uc2dc \ud1a0\ud070 2\uac1c\ub97c \ub4dc\ub9bd\ub2c8\ub2e4.",
    "survey_q1_label": "Q1. \uc5b4\ub5a4 \uc5c5\uc885\uc5d0\uc11c \uc77c\ud558\uace0 \uacc4\uc2e0\uac00\uc694?",
    "survey_q1_placeholder": "\uc120\ud0dd\ud574\uc8fc\uc138\uc694",
    "survey_q1_options": [
        "IT / \uc18c\ud504\ud2b8\uc6e8\uc5b4",
        "\uc81c\uc870\uc5c5",
        "\uc720\ud1b5 / \ucee4\uba38\uc2a4",
        "\uc804\ubb38 \uc11c\ube44\uc2a4 (\ucee8\uc124\ud305, \ud68c\uacc4, \ubc95\ub960 \ub4f1)",
        "\uad50\uc721 / \ud559\uc220",
        "\uac74\uc124 / \ubd80\ub3d9\uc0b0",
        "\ub9c8\ucf00\ud305 / \uad11\uace0 \uc5d0\uc774\uc804\uc2dc",
        "\uae30\ud0c0",
    ],
    "survey_q2_label": "Q2. \uc9c1\ubb34\uac00 \ubb34\uc5c7\uc778\uac00\uc694?",
    "survey_q2_placeholder": "\uc120\ud0dd\ud574\uc8fc\uc138\uc694",
    "survey_q2_options": [
        "\ub300\ud45c / \uacbd\uc601\uc9c4",
        "\uc601\uc5c5 / \uc0ac\uc5c5\uac1c\ubc1c",
        "\ub9c8\ucf00\ud305 / \ube0c\ub79c\ub529",
        "\uae30\ud68d / \uc804\ub7b5",
        "\ub514\uc790\uc778",
        "\uac1c\ubc1c / IT",
        "\uae30\ud0c0",
    ],
    "survey_q3_label": "Q3. \ud68c\uc0ac \uaddc\ubaa8\ub294 \uc5b4\ub290 \uc815\ub3c4\uc778\uac00\uc694?",
    "survey_q3_placeholder": "\uc120\ud0dd\ud574\uc8fc\uc138\uc694",
    "survey_q3_options": [
        "1\uc778 (\ud504\ub9ac\ub79c\uc11c / 1\uc778 \uae30\uc5c5)",
        "2~10\uba85",
        "11~50\uba85",
        "51~200\uba85",
        "200\uba85 \uc774\uc0c1",
    ],
    "survey_q4_label": "Q4. \ud68c\uc0ac\uc18c\uac1c\uc11c\ub294 \uc5bc\ub9c8\ub098 \uc790\uc8fc \ub9cc\ub4dc\uc2dc\ub098\uc694?",
    "survey_q4_placeholder": "\uc120\ud0dd\ud574\uc8fc\uc138\uc694",
    "survey_q4_options": [
        "\uac70\uc758 \uc548 \ub9cc\ub4e0\ub2e4 (\uc5f0 1~2\ud68c)",
        "\uac00\ub054 \ub9cc\ub4e0\ub2e4 (\ubd84\uae30 1~2\ud68c)",
        "\uc790\uc8fc \ub9cc\ub4e0\ub2e4 (\uc6d4 1\ud68c \uc774\uc0c1)",
        "\ub9e4\uc6b0 \uc790\uc8fc \ub9cc\ub4e0\ub2e4 (\uc8fc 1\ud68c \uc774\uc0c1)",
    ],
    "survey_q5_label": "Q5. \uae30\uc874\uc5d0 \uc5b4\ub5bb\uac8c \ub9cc\ub4e4\uace0 \uacc4\uc168\ub098\uc694? (\ubcf5\uc218 \uc120\ud0dd)",
    "survey_q5_options": [
        ("\uc9c1\uc811 \ud30c\uc6cc\ud3ec\uc778\ud2b8\ub85c \uc81c\uc791", "\uc9c1\uc811 \ud30c\uc6cc\ud3ec\uc778\ud2b8\ub85c \uc81c\uc791"),
        ("\uc0ac\ub0b4 \ub514\uc790\uc774\ub108\uc5d0\uac8c \uc694\uccad", "\uc0ac\ub0b4 \ub514\uc790\uc774\ub108\uc5d0\uac8c \uc694\uccad"),
        ("\uc678\uc8fc (\uc5d0\uc774\uc804\uc2dc, \ud504\ub9ac\ub79c\uc11c)", "\uc678\uc8fc"),
        ("\ud15c\ud50c\ub9bf \uc0ac\uc774\ud2b8 (\ubbf8\ub9ac\uce94\ubc84\uc2a4, Canva \ub4f1)", "\ud15c\ud50c\ub9bf \uc0ac\uc774\ud2b8"),
        ("\ub9cc\ub4e0 \uc801 \uc5c6\ub2e4", "\ub9cc\ub4e0 \uc801 \uc5c6\ub2e4"),
    ],
    "survey_q6_label": "Q6. \uc720\ub8cc \uc11c\ube44\uc2a4\uac00 \ub41c\ub2e4\uba74, \uc5b4\ub5a4 \uacb0\uc81c \ubc29\uc2dd\uc744 \uc120\ud638\ud558\uc2dc\ub098\uc694?",
    "survey_q6_placeholder": "\uc120\ud0dd\ud574\uc8fc\uc138\uc694",
    "survey_q6_per_item": "\uac74\ub2f9 \uacb0\uc81c (\ud544\uc694\ud560 \ub54c\ub9cc)",
    "survey_q6_subscription": "\uc6d4 \uc815\uae30 \uad6c\ub3c5",
    "survey_q6_free_only": "\ubb34\ub8cc\uac00 \uc544\ub2c8\uba74 \uc548 \uc4f8 \uac83 \uac19\ub2e4",
    "survey_q7_label": "Q7. \uc801\uc815 \uac00\uaca9\uc740 \uc5b4\ub290 \uc815\ub3c4\ub77c\uace0 \uc0dd\uac01\ud558\uc2dc\ub098\uc694?",
    "survey_q7_placeholder": "\uc120\ud0dd\ud574\uc8fc\uc138\uc694",
    "survey_q8_label": "Q8. \uac00\uc7a5 \ud544\uc694\ud55c \uae30\ub2a5\uc740? (\ucd5c\ub300 3\uac1c)",
    "survey_q8_options": [
        ("\uc6f9\uc5d0\uc11c \uc9c1\uc811 \ud3b8\uc9d1", "\uc6f9\uc5d0\uc11c \uc9c1\uc811 \ud3b8\uc9d1"),
        ("\uc6a9\ub3c4\ubcc4 \ud2b9\ud654 \ud15c\ud50c\ub9bf", "\uc6a9\ub3c4\ubcc4 \ud2b9\ud654 \ud15c\ud50c\ub9bf"),
        ("\uc601\ubb38 \ud68c\uc0ac\uc18c\uac1c\uc11c", "\uc601\ubb38 \ud68c\uc0ac\uc18c\uac1c\uc11c"),
        ("\uc0dd\uc131 \uc774\ub825 \uc800\uc7a5/\uc7ac\ub2e4\uc6b4\ub85c\ub4dc", "\uc774\ub825 \uc800\uc7a5/\uc7ac\ub2e4\uc6b4\ub85c\ub4dc"),
        ("\ud300 \uacc4\uc815", "\ud300 \uacc4\uc815"),
        ("\ube0c\ub79c\ub4dc \uac00\uc774\ub4dc\ub77c\uc778 \uc800\uc7a5", "\ube0c\ub79c\ub4dc \uac00\uc774\ub4dc\ub77c\uc778 \uc800\uc7a5"),
        ("\ud55c \ud398\uc774\uc9c0 \uc694\uc57d PDF", "\ud55c \ud398\uc774\uc9c0 \uc694\uc57d PDF"),
        ("\uacbd\uc7c1\uc0ac \ubd84\uc11d \ud3ec\ud568", "\uacbd\uc7c1\uc0ac \ubd84\uc11d \ud3ec\ud568"),
    ],
    "survey_q9_label": "Q9. \uc790\uc720 \uc758\uacac (\uc120\ud0dd)",
    "survey_q9_placeholder": "\uc608: \uc2ac\ub77c\uc774\ub4dc \ub514\uc790\uc778\uc774 \uc880 \ub354 \ub2e4\uc591\ud588\uc73c\uba74 \uc88b\uaca0\uc5b4\uc694",
    "survey_submit_btn": "\uc124\ubb38 \uc81c\ucd9c\ud558\uace0 \ud1a0\ud070 2\uac1c \ubc1b\uae30",
    "survey_done_title": "\uac10\uc0ac\ud569\ub2c8\ub2e4!",
    "survey_done_msg": "\ud1a0\ud070 2\uac1c\uac00 \uc9c0\uae09\ub418\uc5c8\uc2b5\ub2c8\ub2e4.",
    "survey_done_btn": "\uc2ac\ub77c\uc774\ub4dc \ub9cc\ub4e4\ub7ec \uac00\uae30",

    # ── header ──
    "header_h1": "\ub2f9\uc2e0\uc758 \uc6f9\uc0ac\uc774\ud2b8\ub97c PPT\ub85c",
    "header_p": "URL\uc744 \uc785\ub825\ud558\uba74<br>AI\uac00 \uc790\ub3d9\uc73c\ub85c \ube0c\ub79c\ub4dc \ub9de\ucda4\ud615 \ud504\ub808\uc820\ud14c\uc774\uc158\uc744 \ub9cc\ub4ed\ub2c8\ub2e4.",

    # ── auth section ──
    "auth_title": "\uc2dc\uc791\ud558\uae30",
    "auth_desc": "\ub85c\uadf8\uc778\ud558\uba74 \ubb34\ub8cc \ud1a0\ud070 2\uac1c\uac00 \uc9c0\uae09\ub429\ub2c8\ub2e4",
    "auth_google_btn": "Google\ub85c \uacc4\uc18d\ud558\uae30",
    "auth_tos": '\ub85c\uadf8\uc778 \uc2dc <a href="#" style="color:#6B7685;">\uc774\uc6a9\uc57d\uad00</a> \ubc0f <a href="#" style="color:#6B7685;">\uac1c\uc778\uc815\ubcf4\ucc98\ub9ac\ubc29\uce68</a>\uc5d0 \ub3d9\uc758\ud569\ub2c8\ub2e4',

    # ── form ──
    "form_token_empty": "\ud1a0\ud070\uc744 \ubaa8\ub450 \uc0ac\uc6a9\ud588\uc2b5\ub2c8\ub2e4",
    "form_token_survey_btn": "\ud83d\udccb \uc124\ubb38 \ucc38\uc5ec\ud558\uace0 \ud1a0\ud070 2\uac1c \ubc1b\uae30",
    "form_token_survey_hint": "2~3\ubd84 \uc18c\uc694 \u00b7 \uacc4\uc815\ub2f9 1\ud68c",
    "form_url_label": "\ud648\ud398\uc774\uc9c0 \uc8fc\uc18c",
    "form_company_label": '\ud68c\uc0ac\uba85 <span style="font-weight:400;color:#444">(\uc120\ud0dd)</span>',
    "form_company_placeholder": "\uc790\ub3d9 \uac10\uc9c0\ub429\ub2c8\ub2e4",
    "form_company_hint": "\uc785\ub825\ud558\uc9c0 \uc54a\uc73c\uba74 \ub3c4\uba54\uc778\uc5d0\uc11c \uc790\ub3d9 \ucd94\ucd9c\ud569\ub2c8\ub2e4.",
    "form_purpose_label": "\uc5b4\ub5a4 \uc6a9\ub3c4\uc778\uac00\uc694?",
    "form_purpose_auto": "\u2726 AI \ucd94\ucc9c",
    "form_purpose_brand": "\ube0c\ub79c\ub4dc \uc18c\uac1c",
    "form_purpose_sales": "\uc601\uc5c5 \uc81c\uc548",
    "form_purpose_ir": "\ud22c\uc790 IR",
    "form_purpose_portfolio": "\ud3ec\ud2b8\ud3f4\ub9ac\uc624",
    "form_purpose_report": "\ub0b4\ubd80 \ubcf4\uace0",
    "form_lang_label": "\uc791\uc131 \uc5b8\uc5b4",
    "form_generate_btn": "\uc2ac\ub77c\uc774\ub4dc \uc0dd\uc131\ud558\uae30",
    "form_warning": "\u26a0\ufe0f AI\uac00 \uc0dd\uc131\ud558\ubbc0\ub85c \ub9e4\ubc88 \uacb0\uacfc\uac00 \ub2e4\ub97c \uc218 \uc788\uc2b5\ub2c8\ub2e4 \u00b7 \uc7ac\uc0dd\uc131 \uc2dc \uc774\uc804 \uacb0\uacfc\ub294 \uc0ad\uc81c\ub418\uba70 \ubcf5\uad6c \ubd88\uac00\ud569\ub2c8\ub2e4<br>\uc0dd\uc131\ub41c PPT/PDF\ub294 \ubcf8\uc778\ub9cc \ub2e4\uc6b4\ub85c\ub4dc\ud560 \uc218 \uc788\uc73c\uba70, \uc6b4\uc601\ud300\uc740 \uacb0\uacfc\ubb3c\uc5d0 \uc811\uadfc\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4",

    # ── progress ──
    "progress_title": "AI\uac00 \uc2ac\ub77c\uc774\ub4dc\ub97c \uc0dd\uc131\ud558\uace0 \uc788\uc2b5\ub2c8\ub2e4",
    "progress_desc": "\uc57d 3~5\ubd84 \uc815\ub3c4 \uc18c\uc694\ub429\ub2c8\ub2e4. \uc7a0\uc2dc \uae30\ub2e4\ub824\uc8fc\uc138\uc694.",
    "progress_step1": "\ud648\ud398\uc774\uc9c0 \ubd84\uc11d",
    "progress_step2": "AI \ucf58\ud150\uce20 \uc0dd\uc131",
    "progress_step3": "\uc774\ubbf8\uc9c0 \ud569\uc131",
    "progress_step4": "\uc644\ub8cc",

    # ── done ──
    "done_title": "\uc2ac\ub77c\uc774\ub4dc \uc0dd\uc131 \uc644\ub8cc!",
    "done_slides_label": "\uc2ac\ub77c\uc774\ub4dc",
    "done_narrative_label": "\ub0b4\ub7ec\ud2f0\ube0c \ud0c0\uc785",
    "done_color_title": "\ud074\ub9ad\ud558\uc5ec \ube0c\ub79c\ub4dc \ucee4\ub7ec \ubcc0\uacbd",
    "done_color_label": '\ube0c\ub79c\ub4dc \ucee4\ub7ec <span style="font-size:10px;opacity:0.6;">\u270f\ufe0f</span>',
    "done_reset_btn": "\u21a9 \ub2e4\uc2dc \uc0dd\uc131\ud558\uae30",
    "done_coffee_btn": "\u2615 \ucee4\ud53c \ud55c \uc794 \ud6c4\uc6d0\ud558\uae30",

    # ── edit modal ──
    "edit_modal_title_prefix": "\uc2ac\ub77c\uc774\ub4dc",
    "edit_modal_title_suffix": "\ud3b8\uc9d1",
    "edit_headline_label": "\ud5e4\ub4dc\ub77c\uc778",
    "edit_sub_label": '\uc11c\ube0c\ud5e4\ub4dc\ub77c\uc778 <span style="font-weight:400;color:#555">(\uc120\ud0dd)</span>',
    "edit_body_label": "\ubcf8\ubb38 \ud56d\ubaa9",
    "edit_body_add": "+ \ud56d\ubaa9 \ucd94\uac00",
    "edit_cancel_btn": "\ucde8\uc18c",
    "edit_regen_btn": "\ud83d\udd04 AI \uc7ac\uc0dd\uc131",
    "edit_save_btn": "\uc800\uc7a5",

    # ── error ──
    "error_title": "\uc0dd\uc131 \uc2e4\ud328",
    "error_user_msg": "\uc544\ub798 \uc624\ub958 \ub0b4\uc6a9\uc744 \ud655\uc778\ud574\uc8fc\uc138\uc694.",
    "error_details_btn": "\uc0c1\uc138 \ub85c\uadf8 \ubcf4\uae30",
    "error_retry_btn": "\u21ba \uc7ac\uc2dc\ub3c4",
    "error_reset_btn": "\u21a9 \ucc98\uc74c\uc73c\ub85c",

    # ── step guide ──
    "step_guide_1": "\uc6f9\uc0ac\uc774\ud2b8 \ubd84\uc11d",
    "step_guide_2": "AI \uc2ac\ub77c\uc774\ub4dc \uc81c\uc791",
    "step_guide_3": "PPT \ub2e4\uc6b4\ub85c\ub4dc",

    # ── footer ──
    "footer_feedback_btn": "\ud83d\udcac \ud53c\ub4dc\ubc31",
    "footer_coffee_btn": "\u2615 \ud6c4\uc6d0",

    # ── feedback modal ──
    "feedback_title": "\ud83d\udcac \ud53c\ub4dc\ubc31 \ubcf4\ub0b4\uae30",
    "feedback_desc": "\ubca0\ud0c0 \uc11c\ube44\uc2a4 \uac1c\uc120\uc744 \uc704\ud55c \uc18c\uc911\ud55c \uc758\uacac\uc744 \ubcf4\ub0b4\uc8fc\uc138\uc694",
    "feedback_cat_bug": "\ud83d\udc1b \uc624\ub958 \uc2e0\uace0",
    "feedback_cat_feature": "\ud83d\udca1 \uae30\ub2a5 \uc81c\uc548",
    "feedback_cat_general": "\ud83d\udcac \uae30\ud0c0",
    "feedback_placeholder": "\uc5b4\ub5a4 \uc810\uc774 \ubd88\ud3b8\ud558\uc168\ub098\uc694? \uc5b4\ub5a4 \uae30\ub2a5\uc774 \uc788\uc5c8\uc73c\uba74 \ud558\ub098\uc694?",
    "feedback_submit_btn": "\ubcf4\ub0b4\uae30",
    "feedback_done_title": "\uac10\uc0ac\ud569\ub2c8\ub2e4!",
    "feedback_done_msg": "\uc18c\uc911\ud55c \uc758\uacac\uc740 \uc11c\ube44\uc2a4 \uac1c\uc120\uc5d0 \ubc18\uc601\ud558\uaca0\uc2b5\ub2c8\ub2e4",

    # ── t_js (JavaScript strings) ──
    "t_js": {
        # tokens
        "js_tokens_unit": "\uac1c",
        "js_tokens_insufficient": "\ud1a0\ud070\uc774 \ubd80\uc871\ud569\ub2c8\ub2e4",
        "js_tokens_generate": "\uc2ac\ub77c\uc774\ub4dc \uc0dd\uc131\ud558\uae30",
        "js_tokens_charge_failed": "\ucda9\uc804\uc5d0 \uc2e4\ud328\ud588\uc2b5\ub2c8\ub2e4",

        # coffee modals
        "js_kofi_label": "\ud574\uc678 \uacb0\uc81c",
        "js_coffee_charge_title": "\u2615 \uac1c\ubc1c\uc790\uc5d0\uac8c \ucee4\ud53c \ud55c \uc794?",
        "js_coffee_charge_desc": "\uc11c\ubc84 \uc720\uc9c0\ube44\ub85c \uc18c\uc911\ud788 \uc0ac\uc6a9\ub429\ub2c8\ub2e4",
        "js_coffee_charge_qr_hint": "\ubaa8\ubc14\uc77c: \uc774\ubbf8\uc9c0 \ud074\ub9ad \u00b7 PC: \uce74\uba54\ub77c\ub85c QR \uc2a4\uce94",
        "js_coffee_charge_btn": "\ud83c\udf9f\ufe0f \ud1a0\ud070 2\uac1c \ucda9\uc804\ud558\uae30",
        "js_coffee_modal_title": "\u2615 \ud1a0\ud070 \ucda9\uc804 \uc644\ub8cc!",
        "js_coffee_modal_desc": "\uc774 \uc11c\ube44\uc2a4\uc758 \uc720\uc9c0\ub97c \uc704\ud574<br>\uac1c\ubc1c\uc790\uc5d0\uac8c \ucee4\ud53c \ud55c \uc794\uc740 \uc5b4\ub5a8\uae4c\uc694?",
        "js_coffee_modal_qr_hint": "\ubaa8\ubc14\uc77c: \uc774\ubbf8\uc9c0 \ud074\ub9ad \u00b7 PC: \uce74\uba54\ub77c\ub85c QR \uc2a4\uce94",
        "js_coffee_modal_dismiss": "\ub2e4\uc74c\uc5d0 \ud560\uac8c\uc694",

        # survey status
        "js_survey_charge_btn": "\ud83c\udf9f\ufe0f \ubb34\ub8cc \ud1a0\ud070 2\uac1c \ucda9\uc804",
        "js_survey_charge_hint": "\ubca0\ud0c0 \uae30\uac04 \ubb34\ub8cc \ucda9\uc804",
        "js_survey_required": "Q1~Q4\ub294 \ud544\uc218\uc785\ub2c8\ub2e4",
        "js_survey_q8_max": "Q8\uc740 \ucd5c\ub300 3\uac1c\uae4c\uc9c0 \uc120\ud0dd \uac00\ub2a5\ud569\ub2c8\ub2e4",
        "js_survey_submit_fail": "\uc124\ubb38 \uc81c\ucd9c \uc2e4\ud328",
        "js_survey_server_error": "\uc11c\ubc84 \uc624\ub958",

        # Q7 options
        "js_q7_select": "\uc120\ud0dd\ud574\uc8fc\uc138\uc694",
        "js_q7_per_item_options": '<option value="">\uc120\ud0dd\ud574\uc8fc\uc138\uc694</option><option>1\uac74\ub2f9 3,000\uc6d0 \uc774\ud558</option><option>1\uac74\ub2f9 3,000~5,000\uc6d0</option><option>1\uac74\ub2f9 5,000~10,000\uc6d0</option><option>1\uac74\ub2f9 10,000~30,000\uc6d0</option><option>1\uac74\ub2f9 30,000\uc6d0 \uc774\uc0c1\ub3c4 \uad1c\ucc2e\ub2e4</option>',
        "js_q7_subscription_options": '<option value="">\uc120\ud0dd\ud574\uc8fc\uc138\uc694</option><option>\uc6d4 9,900\uc6d0 (5\uac74)</option><option>\uc6d4 19,900\uc6d0 (10\uac74)</option><option>\uc6d4 29,000\uc6d0 (20\uac74)</option><option>\uc6d4 49,000\uc6d0 (\ubb34\uc81c\ud55c)</option>',

        # history
        "js_history_loading": "\ubd88\ub7ec\uc624\ub294 \uc911...",
        "js_history_empty": "\uc544\uc9c1 \uc0dd\uc131 \uc774\ub825\uc774 \uc5c6\uc2b5\ub2c8\ub2e4",
        "js_history_load_fail": "\ubd88\ub7ec\uc624\uae30 \uc2e4\ud328",
        "js_history_purpose_labels": {"auto": "AI \ucd94\ucc9c", "brand": "\ube0c\ub79c\ub4dc \uc18c\uac1c", "sales": "\uc601\uc5c5 \uc81c\uc548", "ir": "\ud22c\uc790 IR", "portfolio": "\ud3ec\ud2b8\ud3f4\ub9ac\uc624", "report": "\ub0b4\ubd80 \ubcf4\uace0"},
        "js_history_completed": "\uc644\ub8cc",
        "js_history_failed": "\uc2e4\ud328",
        "js_history_processing": "\uc9c4\ud589 \uc911",
        "js_history_no_pdf": "PDF \uc5c6\uc74c",

        # step map
        "js_step_1": "\ud83d\udd0d \uc6f9\uc0ac\uc774\ud2b8\ub97c \ubd84\uc11d\ud558\uace0 \uc788\uc5b4\uc694",
        "js_step_2a": "\ud83d\udccb \ud575\uc2ec \uc815\ubcf4\ub97c \uc815\ub9ac\ud558\uace0 \uc788\uc5b4\uc694",
        "js_step_2b": "\ud83d\udcd0 \uc2ac\ub77c\uc774\ub4dc \uad6c\uc131\uc744 \uc124\uacc4\ud558\uace0 \uc788\uc5b4\uc694",
        "js_step_2c": "\u270d\ufe0f \uc2ac\ub77c\uc774\ub4dc \ub0b4\uc6a9\uc744 \uc791\uc131\ud558\uace0 \uc788\uc5b4\uc694",
        "js_step_3": "\ud83d\uddbc\ufe0f \uc774\ubbf8\uc9c0\ub97c \uc900\ube44\ud558\uace0 \uc788\uc5b4\uc694",
        "js_step_4": "\u2728 \uac70\uc758 \ub2e4 \ub410\uc5b4\uc694!",

        # user visible log
        "js_log_step1": "\ud83d\udd0d \uc6f9\uc0ac\uc774\ud2b8\ub97c \ubd84\uc11d\ud558\uace0 \uc788\uc5b4\uc694... \uc7a0\uc2dc\ub9cc \uae30\ub2e4\ub824\uc8fc\uc138\uc694",
        "js_log_step2": "\ud83c\udfa8 \ube0c\ub79c\ub4dc \ucee4\ub7ec\uc640 \ub85c\uace0\ub97c \ucc3e\uace0 \uc788\uc5b4\uc694...",
        "js_log_step2c": "\ud83d\uddbc\ufe0f \ud648\ud398\uc774\uc9c0 \uc774\ubbf8\uc9c0\ub97c \uc218\uc9d1\ud558\uace0 \uc788\uc5b4\uc694...",
        "js_log_step3a": "\ud83d\udccb \ud575\uc2ec \uc815\ubcf4\ub97c \uc815\ub9ac\ud558\uace0 \uc788\uc5b4\uc694...",
        "js_log_step3b": "\ud83d\udcd0 \uc2ac\ub77c\uc774\ub4dc \uad6c\uc131\uc744 \uc124\uacc4\ud558\uace0 \uc788\uc5b4\uc694...",
        "js_log_step3c": "\u270d\ufe0f \uc2ac\ub77c\uc774\ub4dc \ub0b4\uc6a9\uc744 \uc791\uc131\ud558\uace0 \uc788\uc5b4\uc694...",
        "js_log_step4": "\ud83d\uddbc\ufe0f \uc774\ubbf8\uc9c0\ub97c \uc900\ube44\ud558\uace0 \uc788\uc5b4\uc694...",
        "js_log_done": "\u2705 \uc644\uc131! \uc2ac\ub77c\uc774\ub4dc\ub97c \ud655\uc778\ud558\uc138\uc694",
        "js_log_quality": "\u2728 \ud488\uc9c8\uc744 \uc810\uac80\ud558\uace0 \uc788\uc5b4\uc694...",
        "js_log_reconnect": "\u23f3 \uc5f0\uacb0\uc774 \uc7a0\uc2dc \ub04a\uacbc\uc2b5\ub2c8\ub2e4. \uc7ac\uc5f0\uacb0 \uc911...",

        # download buttons
        "js_download_pptx": "\u2b07 PPTX \ub2e4\uc6b4\ub85c\ub4dc",
        "js_download_pdf": "\u2b07 PDF \ub2e4\uc6b4\ub85c\ub4dc",
        "js_download_loading": "\u23f3 \ub370\uc774\ud130 \ub85c\ub529 \uc911...",
        "js_download_pptx_loading": "\u23f3 PptxGenJS \ub85c\ub529 \uc911...",
        "js_download_pptx_building": "\u23f3 PPTX \uc870\ub9bd \uc911...",
        "js_download_pdf_gen": "\u23f3 PPTX \uc0dd\uc131 \uc911...",
        "js_download_pdf_convert": "\u23f3 PDF \ubcc0\ud658 \uc911...",
        "js_download_load_fail": "\u26a0 \ub85c\ub4dc \uc2e4\ud328 \u2014 \uc0c8\ub85c\uace0\uce68 \ud6c4 \uc2dc\ub3c4",
        "js_download_load_fail_pdf": "\u26a0 \ub85c\ub4dc \uc2e4\ud328",

        # narrative type label
        "js_narrative_labels": {"A": "A\ud615", "B": "B\ud615", "C": "C\ud615", "D": "D\ud615"},

        # error hints
        "js_error_default_title": "\uc0dd\uc131 \uc911 \uc624\ub958\uac00 \ubc1c\uc0dd\ud588\uc2b5\ub2c8\ub2e4.",
        "js_error_default_body": "\uc7a0\uc2dc \ud6c4 \uc7ac\uc2dc\ub3c4\ud574\uc8fc\uc138\uc694. \ubb38\uc81c\uac00 \ubc18\ubcf5\ub418\uba74 URL\uc744 \ud655\uc778\ud558\uac70\ub098 \uad00\ub9ac\uc790\uc5d0\uac8c \ubb38\uc758\ud558\uc138\uc694.",
        "js_error_api_key_title": "API \ud0a4 \uc624\ub958",
        "js_error_api_key_body": ".env \ud30c\uc77c\uc758 GEMINI_API_KEY \ub610\ub294 PEXELS_API_KEY\uac00 \uc62c\ubc14\ub978\uc9c0 \ud655\uc778\ud558\uc138\uc694.",
        "js_error_quota_title": "API \ud638\ucd9c \ud55c\ub3c4 \ucd08\uacfc (429)",
        "js_error_quota_body": "Gemini / Imagen API \ubb34\ub8cc \ud55c\ub3c4\ub97c \ucd08\uacfc\ud588\uc2b5\ub2c8\ub2e4. 1~2\ubd84 \ud6c4 \uc7ac\uc2dc\ub3c4\ud558\uac70\ub098 \uc720\ub8cc \uc694\uae08\uc81c\ub97c \ud655\uc778\ud558\uc138\uc694.",
        "js_error_timeout_title": "\uc694\uccad \uc2dc\uac04 \ucd08\uacfc",
        "js_error_timeout_body": "\uc6f9\ud398\uc774\uc9c0 \ud06c\ub864\ub9c1 \ub610\ub294 API \uc751\ub2f5\uc774 \ub108\ubb34 \uc624\ub798 \uac78\ub838\uc2b5\ub2c8\ub2e4. URL\uc774 \uc811\uadfc \uac00\ub2a5\ud55c\uc9c0 \ud655\uc778 \ud6c4 \uc7ac\uc2dc\ub3c4\ud558\uc138\uc694.",
        "js_error_connection_title": "\uc11c\ubc84 \uc5f0\uacb0 \ub04a\uae40",
        "js_error_connection_body": "\uc11c\ubc84\uc640\uc758 \uc5f0\uacb0\uc774 \ub04a\uc5b4\uc84c\uc2b5\ub2c8\ub2e4. Flask \uc11c\ubc84(app.py)\uac00 \uc2e4\ud589 \uc911\uc778\uc9c0 \ud655\uc778 \ud6c4 \uc7ac\uc2dc\ub3c4\ud558\uc138\uc694.",
        "js_error_parse_title": "AI \uc751\ub2f5 \ud30c\uc2f1 \uc624\ub958",
        "js_error_parse_body": "Gemini\uac00 \uc62c\ubc14\ub974\uc9c0 \uc54a\uc740 \ud615\uc2dd\uc73c\ub85c \uc751\ub2f5\ud588\uc2b5\ub2c8\ub2e4. \uc7ac\uc2dc\ub3c4\ud558\uba74 \ubcf4\ud1b5 \ud574\uacb0\ub429\ub2c8\ub2e4.",
        "js_error_blocked_title": "AI \uc548\uc804 \ud544\ud130 \ucc28\ub2e8",
        "js_error_blocked_body": "URL\uc758 \ucf58\ud150\uce20\uac00 AI \uc548\uc804 \uc815\ucc45\uc5d0 \uc758\ud574 \ucc28\ub2e8\ub418\uc5c8\uc2b5\ub2c8\ub2e4. \ub2e4\ub978 URL\uc744 \uc2dc\ub3c4\ud558\uc138\uc694.",
        "js_error_url_required": "URL\uc744 \uba3c\uc800 \uc785\ub825\ud558\uc138\uc694.",
        "js_error_pptx": "PPTX \uc0dd\uc131 \uc911 \uc624\ub958: ",
        "js_error_pptx_cdn": "PptxGenJS CDN \ub85c\ub4dc \uc2e4\ud328",
        "js_error_pdf_convert_fail": "PDF \ubcc0\ud658 \uc2e4\ud328",
        "js_error_pdf_alert": "PDF \ubcc0\ud658\uc5d0 \uc2e4\ud328\ud588\uc2b5\ub2c8\ub2e4. PPTX\ub97c \uba3c\uc800 \ub2e4\uc6b4\ub85c\ub4dc\ud574 \uc8fc\uc138\uc694.\n",
        "js_error_regen_fail": "AI \uc7ac\uc0dd\uc131\uc5d0 \uc2e4\ud328\ud588\uc2b5\ub2c8\ub2e4",
        "js_error_regen_server": "\uc11c\ubc84 \uc5f0\uacb0 \uc624\ub958: ",

        # edit
        "js_edit_slide_prefix": "\uc2ac\ub77c\uc774\ub4dc ",
        "js_edit_slide_suffix": " \ud3b8\uc9d1",
        "js_edit_no_headline": "(\ud5e4\ub4dc\ub77c\uc778 \uc5c6\uc74c)",
        "js_edit_item_placeholder": "\ud56d\ubaa9 \ud14d\uc2a4\ud2b8",
        "js_edit_delete_title": "\uc0ad\uc81c",
        "js_edit_move_up": "\uc704\ub85c",
        "js_edit_move_down": "\uc544\ub798\ub85c",
        "js_edit_btn": "\ud3b8\uc9d1",
        "js_edit_regen_loading": "\u23f3 \uc0dd\uc131 \uc911...",
        "js_edit_regen_btn": "\ud83d\udd04 AI \uc7ac\uc0dd\uc131",

        # misc
        "js_stitch_count_suffix": "\uc7a5",
        "js_slide_count_suffix": "\uc7a5",
        "js_feedback_sending": "\uc804\uc1a1 \uc911...",
        "js_feedback_submit": "\ubcf4\ub0b4\uae30",
        "js_feedback_fail": "\uc804\uc1a1 \uc2e4\ud328 \u2014 \uc7a0\uc2dc \ud6c4 \ub2e4\uc2dc \uc2dc\ub3c4\ud574\uc8fc\uc138\uc694.",
    },
}


T_EN = {
    # ── meta ──
    "meta_title": "TickDeck \u2014 Turn Your Website into a PPT",
    "meta_desc": "Just enter a URL and AI creates a brand-matched presentation automatically.",
    "meta_canonical": "https://tickdeck.site/en/app",
    "meta_og_title": "TickDeck \u2014 AI Presentation Generator",
    "meta_og_desc": "One URL. AI builds a brand-matched presentation in under 5 minutes.",
    "meta_og_url": "https://tickdeck.site/en/app",

    # ── nav ──
    "nav_home_href": "/en",
    "nav_lang_href": "/app",
    "nav_lang_label": "\ud83c\uddf0\ud83c\uddf7 \ud55c\uad6d\uc5b4",
    "nav_tokens_suffix": "",
    "nav_history_btn": "History",
    "nav_logout_btn": "Logout",

    # ── history modal ──
    "modal_history_title": "Generation History",
    "modal_history_desc": "Only the latest PDF is kept \u00b7 Previous PDF is deleted on regeneration",

    # ── survey modal ──
    "survey_title": "\ud83d\udccb TickDeck Survey",
    "survey_desc": "A quick 2-3 minute survey. Earn 2 tokens on completion.",
    "survey_q1_label": "Q1. What industry?",
    "survey_q1_placeholder": "Select",
    "survey_q1_options": [
        "IT / Software",
        "Manufacturing",
        "Retail / E-commerce",
        "Professional Services",
        "Education",
        "Construction / Real Estate",
        "Marketing / Ad Agency",
        "Other",
    ],
    "survey_q2_label": "Q2. Your role?",
    "survey_q2_placeholder": "Select",
    "survey_q2_options": [
        "CEO / Executive",
        "Sales / BD",
        "Marketing / Branding",
        "Strategy / Planning",
        "Design",
        "Engineering / IT",
        "Other",
    ],
    "survey_q3_label": "Q3. Company size?",
    "survey_q3_placeholder": "Select",
    "survey_q3_options": [
        "Solo (freelancer)",
        "2-10",
        "11-50",
        "51-200",
        "200+",
    ],
    "survey_q4_label": "Q4. How often do you create decks?",
    "survey_q4_placeholder": "Select",
    "survey_q4_options": [
        "Rarely (1-2/year)",
        "Sometimes (1-2/quarter)",
        "Often (1+/month)",
        "Very often (1+/week)",
    ],
    "survey_q5_label": "Q5. Previous method? (multiple)",
    "survey_q5_options": [
        ("Made with PowerPoint", "Made with PowerPoint"),
        ("In-house designer", "In-house designer"),
        ("Outsourced", "Outsourced"),
        ("Template sites (Canva, etc.)", "Template sites (Canva, etc.)"),
        ("Never made one", "Never made one"),
    ],
    "survey_q6_label": "Q6. Payment preference?",
    "survey_q6_placeholder": "Select",
    "survey_q6_per_item": "Per-use (pay as you go)",
    "survey_q6_subscription": "Monthly subscription",
    "survey_q6_free_only": "Wouldn't use if not free",
    "survey_q7_label": "Q7. Fair price?",
    "survey_q7_placeholder": "Select",
    "survey_q8_label": "Q8. Most wanted features? (max 3)",
    "survey_q8_options": [
        ("Edit in browser", "Edit in browser"),
        ("Purpose-specific templates", "Purpose-specific templates"),
        ("Multi-language", "Multi-language"),
        ("Generation history save/re-download", "History save/re-download"),
        ("Team accounts", "Team accounts"),
        ("Brand guideline presets", "Brand guideline presets"),
        ("One-page summary PDF", "One-page summary PDF"),
        ("Competitor analysis", "Competitor analysis"),
    ],
    "survey_q9_label": "Q9. Feedback? (optional)",
    "survey_q9_placeholder": "e.g. I wish there were more slide design options",
    "survey_submit_btn": "Submit Survey &amp; Get 2 Tokens",
    "survey_done_title": "Thank you!",
    "survey_done_msg": "2 tokens have been added!",
    "survey_done_btn": "Start creating slides",

    # ── header ──
    "header_h1": "Turn Your Website into a PPT",
    "header_p": "Enter a URL and<br>AI automatically creates a brand-matched presentation.",

    # ── auth section ──
    "auth_title": "Get Started",
    "auth_desc": "Sign in to get 2 free tokens",
    "auth_google_btn": "Continue with Google",
    "auth_tos": 'By signing in, you agree to our <a href="#" style="color:#6B7685;">Terms of Service</a> and <a href="#" style="color:#6B7685;">Privacy Policy</a>',

    # ── form ──
    "form_token_empty": "All tokens used",
    "form_token_survey_btn": "\ud83d\udccb Take Survey &amp; Get 2 Tokens",
    "form_token_survey_hint": "2-3 min \u00b7 Once per account",
    "form_url_label": "Website URL",
    "form_company_label": 'Company Name <span style="font-weight:400;color:#444">(optional)</span>',
    "form_company_placeholder": "Auto-detected",
    "form_company_hint": "If left empty, it will be extracted from the domain.",
    "form_purpose_label": "What's the purpose?",
    "form_purpose_auto": "\u2726 AI Pick",
    "form_purpose_brand": "Brand Intro",
    "form_purpose_sales": "Sales Proposal",
    "form_purpose_ir": "Investor IR",
    "form_purpose_portfolio": "Portfolio",
    "form_purpose_report": "Internal Report",
    "form_lang_label": "Slide Language",
    "form_generate_btn": "Generate Slides",
    "form_warning": "\u26a0\ufe0f AI-generated results may vary each time \u00b7 Previous results are deleted on regeneration and cannot be recovered<br>Generated PPT/PDF can only be downloaded by you. Our team does not access your content.",

    # ── progress ──
    "progress_title": "AI is generating your slides",
    "progress_desc": "Takes about 3-5 minutes. Please wait.",
    "progress_step1": "Website Analysis",
    "progress_step2": "Crafting Content",
    "progress_step3": "Composing Visuals",
    "progress_step4": "Done",

    # ── done ──
    "done_title": "Slides Generated!",
    "done_slides_label": "Slides",
    "done_narrative_label": "Narrative Type",
    "done_color_title": "Click to change Brand Color",
    "done_color_label": 'Brand Color <span style="font-size:10px;opacity:0.6;">\u270f\ufe0f</span>',
    "done_reset_btn": "\u21a9 Generate Again",
    "done_coffee_btn": "\u2615 Buy me a coffee",

    # ── edit modal ──
    "edit_modal_title_prefix": "Edit Slide",
    "edit_modal_title_suffix": "",
    "edit_headline_label": "\ud5e4\ub4dc\ub77c\uc778",
    "edit_sub_label": '\uc11c\ube0c\ud5e4\ub4dc\ub77c\uc778 <span style="font-weight:400;color:#555">(optional)</span>',
    "edit_body_label": "Body Items",
    "edit_body_add": "+ Add Item",
    "edit_cancel_btn": "\ucde8\uc18c",
    "edit_regen_btn": "\ud83d\udd04 AI \uc7ac\uc0dd\uc131",
    "edit_save_btn": "\uc800\uc7a5",

    # ── error ──
    "error_title": "Generation Failed",
    "error_user_msg": "\uc544\ub798 \uc624\ub958 \ub0b4\uc6a9\uc744 \ud655\uc778\ud574\uc8fc\uc138\uc694.",
    "error_details_btn": "View Details",
    "error_retry_btn": "\u21ba Retry",
    "error_reset_btn": "\u21a9 Start Over",

    # ── step guide ──
    "step_guide_1": "Website Analysis",
    "step_guide_2": "AI Slide Creation",
    "step_guide_3": "PPT Download",

    # ── footer ──
    "footer_feedback_btn": "\ud83d\udcac Feedback",
    "footer_coffee_btn": "\u2615 Support",

    # ── feedback modal ──
    "feedback_title": "\ud83d\udcac Send Feedback",
    "feedback_desc": "Help us improve TickDeck with your feedback",
    "feedback_cat_bug": "\ud83d\udc1b Bug Report",
    "feedback_cat_feature": "\ud83d\udca1 Feature Request",
    "feedback_cat_general": "\ud83d\udcac Other",
    "feedback_placeholder": "What went wrong? What feature would you like to see?",
    "feedback_submit_btn": "Submit",
    "feedback_done_title": "Thank you!",
    "feedback_done_msg": "Your feedback helps us improve TickDeck",

    # ── t_js (JavaScript strings) ──
    "t_js": {
        # tokens
        "js_tokens_unit": "",
        "js_tokens_insufficient": "Not enough tokens",
        "js_tokens_generate": "Generate Slides",
        "js_tokens_charge_failed": "Charge failed",

        # coffee modals
        "js_kofi_label": "International",
        "js_coffee_charge_title": "\u2615 Buy the developer a coffee?",
        "js_coffee_charge_desc": "Helps keep the servers running",
        "js_coffee_charge_qr_hint": "Mobile: tap image \u00b7 PC: scan QR",
        "js_coffee_charge_btn": "\ud83c\udf9f\ufe0f Get 2 Tokens",
        "js_coffee_modal_title": "\u2615 Tokens Recharged!",
        "js_coffee_modal_desc": "Help keep this service running.<br>Buy the developer a coffee?",
        "js_coffee_modal_qr_hint": "Mobile: tap image \u00b7 PC: scan QR",
        "js_coffee_modal_dismiss": "Maybe next time",

        # survey status
        "js_survey_charge_btn": "\ud83c\udf9f\ufe0f Free Token Recharge",
        "js_survey_charge_hint": "Free recharge during beta",
        "js_survey_required": "Q1-Q4 are required",
        "js_survey_q8_max": "Q8: Select up to 3",
        "js_survey_submit_fail": "Survey submission failed",
        "js_survey_server_error": "Server error",

        # Q7 options
        "js_q7_select": "Select",
        "js_q7_per_item_options": '<option value="">Select</option><option>Under \u20a93,000 per item</option><option>\u20a93,000~5,000 per item</option><option>\u20a95,000~10,000 per item</option><option>\u20a910,000~30,000 per item</option><option>Over \u20a930,000 is fine</option>',
        "js_q7_subscription_options": '<option value="">Select</option><option>\u20a99,900/mo (5 slides)</option><option>\u20a919,900/mo (10 slides)</option><option>\u20a929,000/mo (20 slides)</option><option>\u20a949,000/mo (unlimited)</option>',

        # history
        "js_history_loading": "Loading...",
        "js_history_empty": "No generation history yet",
        "js_history_load_fail": "Failed to load",
        "js_history_purpose_labels": {"auto": "AI \ucd94\ucc9c", "brand": "Brand Intro", "sales": "Sales Proposal", "ir": "Investor IR", "portfolio": "Portfolio", "report": "Internal Report"},
        "js_history_completed": "Completed",
        "js_history_failed": "Failed",
        "js_history_processing": "Processing",
        "js_history_no_pdf": "PDF \uc5c6\uc74c",

        # step map
        "js_step_1": "\ud83d\udd0d Analyzing website",
        "js_step_2a": "\ud83d\udccb Extracting key information",
        "js_step_2b": "\ud83d\udcd0 Designing slide structure",
        "js_step_2c": "\u270d\ufe0f Writing slide content",
        "js_step_3": "\ud83d\uddbc\ufe0f Preparing images",
        "js_step_4": "\u2728 Almost done!",

        # user visible log
        "js_log_step1": "\ud83d\udd0d Analyzing website... may take a minute for complex sites",
        "js_log_step2": "\ud83c\udfa8 Detecting brand colors and logo...",
        "js_log_step2c": "\ud83d\uddbc\ufe0f Collecting images...",
        "js_log_step3a": "\ud83d\udccb Extracting key information...",
        "js_log_step3b": "\ud83d\udcd0 Designing slide structure...",
        "js_log_step3c": "\u270d\ufe0f Writing slide content...",
        "js_log_step4": "\ud83d\uddbc\ufe0f Preparing images...",
        "js_log_done": "\u2705 Done! Check your slides",
        "js_log_quality": "\u2728 Quality check in progress...",
        "js_log_reconnect": "\u23f3 Connection lost. Reconnecting...",

        # download buttons
        "js_download_pptx": "\u2b07 Download PPTX",
        "js_download_pdf": "\u2b07 Download PDF",
        "js_download_loading": "\u23f3 Loading data...",
        "js_download_pptx_loading": "\u23f3 Loading PptxGenJS...",
        "js_download_pptx_building": "\u23f3 Building PPTX...",
        "js_download_pdf_gen": "\u23f3 Generating PPTX...",
        "js_download_pdf_convert": "\u23f3 Converting to PDF...",
        "js_download_load_fail": "\u26a0 Load failed \u2014 please refresh",
        "js_download_load_fail_pdf": "\u26a0 Load failed",

        # narrative type label
        "js_narrative_labels": {"A": "Type A", "B": "Type B", "C": "Type C", "D": "Type D"},

        # error hints
        "js_error_default_title": "An error occurred during generation.",
        "js_error_default_body": "Please retry shortly. If the problem persists, check the URL or contact support.",
        "js_error_api_key_title": "API Key Error",
        "js_error_api_key_body": ".env \ud30c\uc77c\uc758 GEMINI_API_KEY \ub610\ub294 PEXELS_API_KEY\uac00 \uc62c\ubc14\ub978\uc9c0 \ud655\uc778\ud558\uc138\uc694.",
        "js_error_quota_title": "API Rate Limit Exceeded",
        "js_error_quota_body": "Gemini / Imagen API \ubb34\ub8cc \ud55c\ub3c4\ub97c \ucd08\uacfc\ud588\uc2b5\ub2c8\ub2e4. 1~2\ubd84 \ud6c4 Retry\ud558\uac70\ub098 \uc720\ub8cc \uc694\uae08\uc81c\ub97c \ud655\uc778\ud558\uc138\uc694.",
        "js_error_timeout_title": "Request Timeout",
        "js_error_timeout_body": "\uc6f9\ud398\uc774\uc9c0 \ud06c\ub864\ub9c1 \ub610\ub294 API \uc751\ub2f5\uc774 \ub108\ubb34 \uc624\ub798 \uac78\ub838\uc2b5\ub2c8\ub2e4. URL\uc774 \uc811\uadfc \uac00\ub2a5\ud55c\uc9c0 \ud655\uc778 \ud6c4 Retry\ud558\uc138\uc694.",
        "js_error_connection_title": "Server Disconnected",
        "js_error_connection_body": "\uc11c\ubc84\uc640\uc758 \uc5f0\uacb0\uc774 \ub04a\uc5b4\uc84c\uc2b5\ub2c8\ub2e4. Flask \uc11c\ubc84(app.py)\uac00 \uc2e4\ud589 \uc911\uc778\uc9c0 \ud655\uc778 \ud6c4 Retry\ud558\uc138\uc694.",
        "js_error_parse_title": "AI Response Error",
        "js_error_parse_body": "Gemini\uac00 \uc62c\ubc14\ub974\uc9c0 \uc54a\uc740 \ud615\uc2dd\uc73c\ub85c \uc751\ub2f5\ud588\uc2b5\ub2c8\ub2e4. Retry\ud558\uba74 \ubcf4\ud1b5 \ud574\uacb0\ub429\ub2c8\ub2e4.",
        "js_error_blocked_title": "Content Blocked",
        "js_error_blocked_body": "URL\uc758 \ucf58\ud150\uce20\uac00 AI \uc548\uc804 \uc815\ucc45\uc5d0 \uc758\ud574 \ucc28\ub2e8\ub418\uc5c8\uc2b5\ub2c8\ub2e4. \ub2e4\ub978 URL\uc744 \uc2dc\ub3c4\ud558\uc138\uc694.",
        "js_error_url_required": "Please enter a URL first.",
        "js_error_pptx": "PPTX generation error: ",
        "js_error_pptx_cdn": "PptxGenJS CDN Load failed",
        "js_error_pdf_convert_fail": "PDF \ubcc0\ud658 \uc2e4\ud328",
        "js_error_pdf_alert": "PDF conversion failed. Please download PPTX first.\n",
        "js_error_regen_fail": "AI regeneration failed",
        "js_error_regen_server": "Server connection error: ",

        # edit
        "js_edit_slide_prefix": "Edit Slide ",
        "js_edit_slide_suffix": "",
        "js_edit_no_headline": "(No headline)",
        "js_edit_item_placeholder": "Item text",
        "js_edit_delete_title": "Delete",
        "js_edit_move_up": "Move up",
        "js_edit_move_down": "Move down",
        "js_edit_btn": "Edit",
        "js_edit_regen_loading": "\u23f3 Generating...",
        "js_edit_regen_btn": "\ud83d\udd04 AI Regenerate",

        # misc
        "js_stitch_count_suffix": " slides",
        "js_slide_count_suffix": " slides",
        "js_feedback_sending": "Sending...",
        "js_feedback_submit": "Submit",
        "js_feedback_fail": "Failed to send. Please try again.",
    },
}
