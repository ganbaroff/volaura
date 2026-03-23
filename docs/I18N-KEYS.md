# Volaura i18n Keys — Complete Reference

> Supplementary file for MEGA-PROMPT.md
> All keys are required. ZERO hardcoded strings allowed.
> AZ is primary language, EN is secondary.

---

## common.json (~35 keys)
```json
{
  "app_name": { "az": "Volaura", "en": "Volaura" },
  "tagline": { "az": "Təsdiqlənmiş könüllü bacarıqları", "en": "Verified volunteer credentials" },
  "nav": {
    "dashboard": { "az": "İdarə paneli", "en": "Dashboard" },
    "assessment": { "az": "Qiymətləndirmə", "en": "Assessment" },
    "profile": { "az": "Profil", "en": "Profile" },
    "leaderboard": { "az": "Lider cədvəli", "en": "Leaderboard" },
    "events": { "az": "Tədbirlər", "en": "Events" },
    "settings": { "az": "Parametrlər", "en": "Settings" },
    "notifications": { "az": "Bildirişlər", "en": "Notifications" }
  },
  "actions": {
    "save": { "az": "Saxla", "en": "Save" },
    "cancel": { "az": "Ləğv et", "en": "Cancel" },
    "delete": { "az": "Sil", "en": "Delete" },
    "edit": { "az": "Redaktə et", "en": "Edit" },
    "submit": { "az": "Göndər", "en": "Submit" },
    "continue": { "az": "Davam et", "en": "Continue" },
    "back": { "az": "Geri", "en": "Back" },
    "close": { "az": "Bağla", "en": "Close" },
    "share": { "az": "Paylaş", "en": "Share" },
    "copy_link": { "az": "Linki kopyala", "en": "Copy link" },
    "copied": { "az": "Kopyalandı!", "en": "Copied!" },
    "retry": { "az": "Yenidən cəhd et", "en": "Retry" },
    "loading": { "az": "Yüklənir...", "en": "Loading..." },
    "search": { "az": "Axtar", "en": "Search" },
    "filter": { "az": "Filtrlə", "en": "Filter" },
    "sort": { "az": "Sırala", "en": "Sort" },
    "view_all": { "az": "Hamısına bax", "en": "View all" },
    "sign_out": { "az": "Çıxış", "en": "Sign out" }
  },
  "empty_state": {
    "no_data": { "az": "Hələ məlumat yoxdur", "en": "No data yet" },
    "no_results": { "az": "Nəticə tapılmadı", "en": "No results found" }
  },
  "language": {
    "az": { "az": "Azərbaycan dili", "en": "Azerbaijani" },
    "en": { "az": "İngilis dili", "en": "English" }
  }
}
```

## auth.json (~18 keys)
```json
{
  "login": {
    "title": { "az": "Volaura-ya daxil olun", "en": "Sign in to Volaura" },
    "subtitle": { "az": "Könüllülük bacarıqlarınızı kəşf edin", "en": "Discover your volunteer potential" },
    "email_placeholder": { "az": "E-poçt ünvanınız", "en": "Your email address" },
    "magic_link_button": { "az": "Giriş linki göndər", "en": "Send magic link" },
    "or_divider": { "az": "və ya", "en": "or" },
    "google_button": { "az": "Google ilə davam et", "en": "Continue with Google" },
    "magic_link_sent": { "az": "Giriş linki göndərildi! E-poçtunuzu yoxlayın.", "en": "Magic link sent! Check your email." },
    "magic_link_error": { "az": "Link göndərilə bilmədi. Yenidən cəhd edin.", "en": "Couldn't send the link. Please try again." }
  },
  "callback": {
    "verifying": { "az": "Doğrulanır...", "en": "Verifying..." },
    "error": { "az": "Doğrulama uğursuz oldu", "en": "Verification failed" }
  },
  "signup": {
    "complete_profile": { "az": "Profilinizi tamamlayın", "en": "Complete your profile" },
    "username_label": { "az": "İstifadəçi adı", "en": "Username" },
    "full_name_label": { "az": "Tam ad", "en": "Full name" },
    "city_label": { "az": "Şəhər", "en": "City" }
  },
  "legal": {
    "terms": { "az": "İstifadə şərtləri", "en": "Terms of Service" },
    "privacy": { "az": "Məxfilik siyasəti", "en": "Privacy Policy" },
    "agree": { "az": "Davam etməklə şərtləri qəbul edirsiniz", "en": "By continuing, you agree to the terms" }
  }
}
```

## assessment.json (~45 keys)
```json
{
  "hub": {
    "title": { "az": "Bacarıq qiymətləndirməsi", "en": "Skills Assessment" },
    "subtitle": { "az": "8 bacarığınızı qiymətləndirin", "en": "Evaluate your 8 competencies" },
    "start_button": { "az": "Başla", "en": "Start" },
    "continue_button": { "az": "Davam et", "en": "Continue" },
    "completed_label": { "az": "Tamamlandı", "en": "Completed" },
    "not_started": { "az": "Başlanmayıb", "en": "Not started" },
    "in_progress": { "az": "Davam edir", "en": "In progress" },
    "estimated_time": { "az": "Təxmini vaxt: {{minutes}} dəq", "en": "Est. time: {{minutes}} min" }
  },
  "competencies": {
    "communication": { "az": "Ünsiyyət", "en": "Communication" },
    "reliability": { "az": "Etibarlılıq", "en": "Reliability" },
    "english_proficiency": { "az": "İngilis dili bilikləri", "en": "English Proficiency" },
    "leadership": { "az": "Liderlik", "en": "Leadership" },
    "event_performance": { "az": "Tədbir performansı", "en": "Event Performance" },
    "tech_literacy": { "az": "Texnoloji savadlılıq", "en": "Tech Literacy" },
    "adaptability": { "az": "Uyğunlaşma", "en": "Adaptability" },
    "empathy_safeguarding": { "az": "Empatiya və qoruma", "en": "Empathy & Safeguarding" }
  },
  "question": {
    "progress": { "az": "Sual {{current}}/{{total}}", "en": "Question {{current}}/{{total}}" },
    "difficulty": {
      "1": { "az": "Asan", "en": "Easy" },
      "2": { "az": "Orta", "en": "Medium" },
      "3": { "az": "Çətin", "en": "Hard" }
    },
    "bars_instruction": { "az": "Aşağıdakı şkalada özünüzü qiymətləndirin", "en": "Rate yourself on the scale below" },
    "mcq_instruction": { "az": "Bir cavab seçin", "en": "Select one answer" },
    "open_text_instruction": { "az": "Cavabınızı yazın (maksimum {{max}} söz)", "en": "Write your answer (max {{max}} words)" },
    "word_count": { "az": "{{count}}/{{max}} söz", "en": "{{count}}/{{max}} words" },
    "ai_evaluation": { "az": "AI tərəfindən qiymətləndiriləcək", "en": "Will be evaluated by AI" },
    "submit_answer": { "az": "Cavabı göndər", "en": "Submit answer" },
    "next_question": { "az": "Növbəti sual", "en": "Next question" },
    "evaluating": { "az": "AI qiymətləndirir...", "en": "AI is evaluating..." },
    "time_spent": { "az": "Vaxt: {{seconds}} san", "en": "Time: {{seconds}}s" }
  },
  "complete": {
    "title": { "az": "Qiymətləndirmə tamamlandı!", "en": "Assessment complete!" },
    "calculating": { "az": "AURA balınız hesablanır...", "en": "Calculating your AURA score..." },
    "all_done_title": { "az": "Bütün qiymətləndirmələr tamamlandı!", "en": "All assessments complete!" },
    "view_results": { "az": "Nəticələrə bax", "en": "View results" }
  },
  "resume": {
    "title": { "az": "Davam etmək istəyirsiniz?", "en": "Continue where you left off?" },
    "yes": { "az": "Bəli, davam et", "en": "Yes, continue" },
    "restart": { "az": "Yenidən başla", "en": "Start over" }
  }
}
```

## results.json (~32 keys)
```json
{
  "score": {
    "your_aura": { "az": "Sizin AURA balınız", "en": "Your AURA Score" },
    "percentile": { "az": "Siz könüllülərin {{percent}}%-dən yaxşısınız", "en": "Better than {{percent}}% of volunteers" },
    "history": { "az": "Bal tarixçəsi", "en": "Score history" },
    "improve": { "az": "Balınızı yaxşılaşdırın", "en": "Improve your score" },
    "reassess": { "az": "Yenidən qiymətləndir", "en": "Reassess" }
  },
  "badge": {
    "platinum": { "az": "Platinum", "en": "Platinum" },
    "gold": { "az": "Qızıl", "en": "Gold" },
    "silver": { "az": "Gümüş", "en": "Silver" },
    "bronze": { "az": "Bürünc", "en": "Bronze" },
    "none": { "az": "Başlanğıc", "en": "Starter" },
    "congratulations": { "az": "Təbrik edirik! 🎉", "en": "Congratulations! 🎉" },
    "you_earned": { "az": "Siz {{tier}} nişanı qazandınız!", "en": "You earned the {{tier}} badge!" },
    "badge_changed": { "az": "Nişanınız {{old}} → {{new}} dəyişdi!", "en": "Badge changed from {{old}} to {{new}}!" }
  },
  "competency_breakdown": {
    "title": { "az": "Bacarıq təhlili", "en": "Competency Breakdown" },
    "weight": { "az": "Çəki: {{weight}}%", "en": "Weight: {{weight}}%" },
    "verification": {
      "self_assessed": { "az": "Özünü qiymətləndirmə", "en": "Self-assessed" },
      "org_attested": { "az": "Təşkilat təsdiqli", "en": "Org-attested" },
      "peer_verified": { "az": "Həmyaşıd təsdiqli", "en": "Peer-verified" }
    }
  },
  "share": {
    "title": { "az": "Balınızı paylaşın", "en": "Share your score" },
    "linkedin": { "az": "LinkedIn-də paylaş", "en": "Share on LinkedIn" },
    "instagram": { "az": "Instagram Story", "en": "Instagram Story" },
    "square": { "az": "Şəkil kimi saxla", "en": "Save as image" },
    "copy_link": { "az": "Profil linkini kopyala", "en": "Copy profile link" },
    "qr_code": { "az": "QR kodu göstər", "en": "Show QR code" },
    "share_text": { "az": "Mən Volaura-da {{score}} bal topladım! {{tier}} könüllüyəm 🌟", "en": "I scored {{score}} on Volaura! {{tier}} volunteer 🌟" }
  },
  "radar": {
    "title": { "az": "Bacarıq radarı", "en": "Skill Radar" },
    "tap_for_detail": { "az": "Təfərrüat üçün toxunun", "en": "Tap axis for detail" }
  }
}
```

## profile.json (~28 keys)
```json
{
  "my_profile": { "az": "Mənim profilim", "en": "My Profile" },
  "public_profile": { "az": "İctimai profil", "en": "Public Profile" },
  "edit_profile": { "az": "Profili redaktə et", "en": "Edit Profile" },
  "share_profile": { "az": "Profili paylaş", "en": "Share Profile" },
  "fields": {
    "full_name": { "az": "Tam ad", "en": "Full name" },
    "username": { "az": "İstifadəçi adı", "en": "Username" },
    "bio": { "az": "Haqqında", "en": "Bio" },
    "bio_placeholder": { "az": "Özünüz haqqında qısa məlumat...", "en": "Tell us about yourself..." },
    "city": { "az": "Şəhər", "en": "City" },
    "country": { "az": "Ölkə", "en": "Country" },
    "expertise": { "az": "Bacarıqlar", "en": "Expertise" },
    "languages": { "az": "Dillər", "en": "Languages" },
    "avatar": { "az": "Profil şəkli", "en": "Profile photo" },
    "upload_avatar": { "az": "Şəkil yüklə", "en": "Upload photo" }
  },
  "visibility": {
    "public": { "az": "İctimai profil", "en": "Public profile" },
    "private": { "az": "Gizli profil", "en": "Private profile" },
    "toggle_label": { "az": "Profil görünürlüğü", "en": "Profile visibility" }
  },
  "verification": {
    "title": { "az": "Doğrulama səviyyəsi", "en": "Verification Level" },
    "self_assessed": { "az": "Özünü qiymətləndirmə", "en": "Self-assessed" },
    "org_attested": { "az": "Təşkilat təsdiqli", "en": "Organization verified" },
    "peer_verified": { "az": "Həmyaşıd təsdiqli", "en": "Peer verified" }
  },
  "events": {
    "history_title": { "az": "Tədbir tarixçəsi", "en": "Event History" },
    "no_events": { "az": "Hələ heç bir tədbirə qatılmamısınız", "en": "No events attended yet" },
    "attended": { "az": "İştirak etdi", "en": "Attended" },
    "events_count": { "az": "{{count}} tədbir", "en": "{{count}} events" }
  },
  "public_cta": {
    "join_volaura": { "az": "Volaura-ya qoşulun", "en": "Join Volaura" },
    "discover_potential": { "az": "Könüllülük potensialınızı kəşf edin", "en": "Discover your volunteer potential" }
  }
}
```

## events.json (~22 keys)
```json
{
  "list": {
    "title": { "az": "Tədbirlər", "en": "Events" },
    "find_events": { "az": "Tədbir tap", "en": "Find events" },
    "my_events": { "az": "Mənim tədbirlərim", "en": "My events" },
    "no_events": { "az": "Hazırda tədbir yoxdur", "en": "No events available" }
  },
  "filter": {
    "date": { "az": "Tarix", "en": "Date" },
    "location": { "az": "Məkan", "en": "Location" },
    "min_aura": { "az": "Minimum AURA", "en": "Min AURA" },
    "competency": { "az": "Bacarıq", "en": "Competency" },
    "sort_date": { "az": "Tarixə görə", "en": "By date" },
    "sort_popularity": { "az": "Populyarlığa görə", "en": "By popularity" }
  },
  "detail": {
    "organized_by": { "az": "Təşkilatçı: {{org}}", "en": "Organized by {{org}}" },
    "date_range": { "az": "{{start}} — {{end}}", "en": "{{start}} — {{end}}" },
    "location": { "az": "Məkan", "en": "Location" },
    "requirements": { "az": "Tələblər", "en": "Requirements" },
    "min_aura_required": { "az": "Minimum AURA: {{score}}", "en": "Min AURA: {{score}}" },
    "capacity": { "az": "{{current}}/{{max}} yer tutulub", "en": "{{current}}/{{max}} spots filled" },
    "register_button": { "az": "Qeydiyyatdan keç", "en": "Register" },
    "already_registered": { "az": "Qeydiyyatdasınız ✓", "en": "Registered ✓" },
    "aura_too_low": { "az": "AURA balınız kifayət deyil ({{required}} tələb olunur)", "en": "AURA score too low ({{required}} required)" },
    "event_full": { "az": "Tədbir dolub", "en": "Event is full" }
  },
  "status": {
    "registered": { "az": "Qeydiyyatda", "en": "Registered" },
    "attended": { "az": "İştirak etdi", "en": "Attended" },
    "no_show": { "az": "Gəlmədi", "en": "No show" },
    "cancelled": { "az": "Ləğv edildi", "en": "Cancelled" }
  }
}
```

## errors.json (~18 keys)
```json
{
  "UNAUTHORIZED": { "az": "Autentifikasiya tələb olunur", "en": "Authentication required" },
  "FORBIDDEN": { "az": "Giriş qadağandır", "en": "Access denied" },
  "PROFILE_NOT_FOUND": { "az": "Profil tapılmadı", "en": "Profile not found" },
  "ASSESSMENT_NOT_FOUND": { "az": "Qiymətləndirmə tapılmadı", "en": "Assessment not found" },
  "EVENT_NOT_FOUND": { "az": "Tədbir tapılmadı", "en": "Event not found" },
  "EVENT_FULL": { "az": "Tədbir dolub", "en": "Event is at full capacity" },
  "ALREADY_REGISTERED": { "az": "Artıq qeydiyyatdan keçmisiniz", "en": "Already registered" },
  "INSUFFICIENT_AURA": { "az": "AURA balınız bu tədbir üçün kifayət deyil", "en": "AURA score too low for this event" },
  "ASSESSMENT_ALREADY_COMPLETE": { "az": "Bu bacarıq artıq qiymətləndirilib", "en": "This competency is already assessed" },
  "COMPETENCY_IN_PROGRESS": { "az": "Bu bacarıq üçün qiymətləndirmə davam edir", "en": "Assessment in progress for this competency" },
  "INVALID_ANSWER_FORMAT": { "az": "Yanlış cavab formatı", "en": "Invalid answer format" },
  "RATE_LIMIT_EXCEEDED": { "az": "Çox sorğu göndərdiniz. Bir az gözləyin", "en": "Too many requests. Please wait" },
  "LLM_EVALUATION_FAILED": { "az": "AI qiymətləndirmə müvəqqəti əlçatmazdır", "en": "AI evaluation temporarily unavailable" },
  "NETWORK_ERROR": { "az": "Şəbəkə xətası. Yenidən cəhd edin", "en": "Network error. Please retry" },
  "GENERIC_ERROR": { "az": "Xəta baş verdi", "en": "Something went wrong" },
  "UPGRADE_REQUIRED": { "az": "Bu funksiya üçün ödənişli plan tələb olunur", "en": "Paid plan required for this feature" },
  "EVALUATION_PENDING": { "az": "Cavab saxlanıldı, AI qiymətləndirmə davam edir", "en": "Answer saved, AI evaluation in progress" }
}
```
