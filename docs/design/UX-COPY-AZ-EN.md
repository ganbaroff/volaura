# Volaura UX Copy Reference: Azerbaijani + English

**Last Updated:** 2026-03-22
**Scope:** Complete microcopy catalog for all user-facing text
**Primary Language:** Azerbaijani (AZ) with formal "Siz" register
**Secondary Language:** English (EN)
**i18n Location:** `public/locales/{locale}/{namespace}.json`

---

## Translation Notes

### Azerbaijani Conventions
- Use formal "Siz" (capital S) throughout for respect
- Character set: ə, ğ, ı, ö, ü, ş, ç (verify in font)
- Text expansion: typically 20–30% longer than English
- Verb-final word order in technical descriptions
- Currency: AZN (₼) when displaying prices
- Date format: DD.MM.YYYY

### English Conventions
- Use American English spelling (behavior, color, optimize)
- Keep sentences short (max 12–15 words for mobile readability)
- Use active voice, second person ("you") when possible
- Avoid jargon; define AURA on first mention

### Namespaces in i18n
Organize translation files by feature:
- `common.json` — shared strings, buttons, headers
- `auth.json` — login, signup, magic link
- `assessment.json` — questions, scales, progress
- `results.json` — scores, badges, recommendations
- `profile.json` — profile editing, verification
- `events.json` — event listing, registration
- `organization.json` — org dashboard, attestation
- `notifications.json` — notification templates
- `errors.json` — error messages, validation

---

## 1. Navigation

**Sidebar & Navigation Labels**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| nav.dashboard | Dashboard | Paneli | Main hub after login |
| nav.assessment | Assessment | Qiymətləndirmə | Take or review assessments |
| nav.events | Events | Tədbirlər | Discover and register for events |
| nav.profile | Profile | Profil | View and edit personal info |
| nav.settings | Settings | Ayarlar | Account, preferences, privacy |
| nav.help | Help & Support | Kömək & Dəstək | FAQ, contact support |
| nav.logout | Log Out | Çıxış | Sign out of account |

**Topbar & Section Headers**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| topbar.welcome | Welcome, {name} | Xoş gəlmisiniz, {name} | Personalized greeting |
| topbar.notification | Notifications | Bildirişlər | Unread count badge |
| topbar.language | Language | Dil | Switch between AZ/EN |
| section.recentActivity | Recent Activity | Son Fəaliyyət | Dashboard widget |
| section.yourScore | Your AURA Score | Sizin AURA Xalınız | Results section header |
| section.upcomingEvents | Upcoming Events | Qacoming Tədbirlər | Events list header |

**Mobile Bottom Navigation**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| nav.mobile.home | Home | Ev | Dashboard tab icon |
| nav.mobile.assess | Assess | Qiymətləndirmə | Assessment tab icon |
| nav.mobile.events | Events | Tədbirlər | Events tab icon |
| nav.mobile.profile | Profile | Profil | Profile tab icon |
| nav.mobile.menu | Menu | Menyü | More options tab icon |

---

## 2. Authentication

**Login & Signup Screen**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| auth.enterEmail | Enter your email to get started | Başlamaq üçün e-poçtunuzu daxil edin | Email input label |
| auth.emailPlaceholder | you@example.com | sizə@nümunə.az | Email input placeholder |
| auth.sendLink | Send Magic Link | Sehrli Keçidi Göndər | CTA button |
| auth.or | or | və ya | Divider between login methods |
| auth.phoneLogin | Continue with Phone | Telefon ilə Davam etmək | Alternative auth (future) |
| auth.alreadyHaveAccount | Already have an account? Log in | Artıq hesabınız var? Daxil olun | Link to login from signup |
| auth.noAccount | Don't have an account? Sign up | Hesabınız yoxdur? Qeydiyyatdan keçin | Link to signup from login |

**Magic Link Email**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| auth.emailSubject | Your Volaura Magic Link | Volaura Sehrli Keçidiniz | Email subject line |
| auth.emailBody | Click the link below to log in. This link expires in 24 hours. | Daxil olmaq üçün aşağıdakı keçidə klikləyin. Bu keçid 24 saat ərzində sona çatacaq. | Email body text |
| auth.copyLink | Copy Link | Keçidi Kopyala | Copy link button |
| auth.didNotRequest | Didn't request this? Ignore this email. | Bunu tələb etmədiniz? Bu e-poçtu saymazsız. | Security note |

**Magic Link Verification Page**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| auth.checkInbox | Check your inbox for the magic link | Sehrli keçid üçün gələnlər qutunuzu yoxlayın | Instruction after email sent |
| auth.checkSpam | If you don't see it, check your spam folder. | Görmüsünüzsə, spam qutunuzu yoxlayın. | Help text |
| auth.resendLink | Resend Link | Keçidi Yenidən Göndər | Resend button (after 60s) |
| auth.linkExpired | This link has expired. | Bu keçid sona çatmışdır. | Error message |
| auth.verifying | Verifying... | Təsdiqlənir... | Loading state during verification |
| auth.success | Welcome to Volaura! | Volaura-ya xoş gəlmisiniz! | Success confirmation |

**Error Messages**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| errors.invalidEmail | Please enter a valid email address | Zəhmət olmasa düzgün e-poçt ünvanı daxil edin | Email validation error |
| errors.sessionExpired | Your session has expired. Please log in again. | Sizin sessiya sona çatmışdır. Zəhmət olmasa yenidən daxil olun. | Session timeout |
| errors.tooManyAttempts | Too many login attempts. Try again in 15 minutes. | Çox çox dəfə cəhd edin. 15 dəqiqədan sonra cəhd edin. | Rate limit |
| errors.accountLocked | Your account is temporarily locked. Contact support. | Sizin hesab müvəqqəti olaraq kilidlənib. Dəstəklə əlaqə saxlayın. | Security lockout |

---

## 3. Onboarding

**Onboarding Flow (4 Steps)**

### Step 1: Welcome

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| onboard.step1.title | Welcome to Volaura | Volaura-ya Xoş Gəlmisiniz | Step 1 hero title |
| onboard.step1.desc | Discover your volunteer credentials and connect with opportunities that match your skills. | Könüllü kimlik məlumatlarınızı kəşf edin və bacarıqlarınıza uyğun imkanlarla əlaqə saxlayın. | Step 1 description |
| onboard.step1.cta | Next | Sonrakı | CTA button |

### Step 2: What is AURA?

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| onboard.step2.title | Meet Your AURA Score | AURA Xalınız ilə Tanış Olun | Step 2 hero title |
| onboard.step2.desc | AURA measures 8 core competencies: communication, reliability, English proficiency, leadership, event performance, tech literacy, adaptability, and empathy. Your score unlocks verified opportunities. | AURA 8 əsas bacarığı ölçür: kommunikasiya, etibarlılıq, İngilis dili bilikləri, liderlik, tədbir performansı, texniki savadlılıq, uyğunlaşdırılabilirlik və empati. Sizin xalınız təsdiqlənmiş imkanları açır. | Step 2 explanation |
| onboard.step2.cta | Continue | Davam etmək | CTA button |
| onboard.competencies.list | Communication, Reliability, English Proficiency, Leadership, Event Performance, Tech Literacy, Adaptability, Empathy & Safeguarding | Kommunikasiya, Etibarlılıq, İngilis Dili, Liderlik, Tədbir Performansı, Texniki Savadlılıq, Uyğunlaşdırılabilirlik, Empati | 8-competency list |

### Step 3: Take Assessment

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| onboard.step3.title | Ready to Discover Your AURA? | AURA-nı Kəşf Etməyə Hazırsınız? | Step 3 hero title |
| onboard.step3.desc | Take a 10–15 minute assessment to reveal your AURA score. You can retake it once every 30 days. | 10–15 dəqiqəlik qiymətləndirmə keçin AURA xalınızı ortaya qoymaq üçün. Hər 30 gündən bir yenidən keçə bilərsiniz. | Step 3 description |
| onboard.step3.cta | Start Assessment | Qiymətləndirməni Başlat | CTA button |

### Step 4: Share & Connect

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| onboard.step4.title | Share Your Achievement | Uğurunuzu Paylaş | Step 4 hero title |
| onboard.step4.desc | Share your AURA badge on social media, or copy your public profile link to stand out to event organizers. | AURA nişanını sosial mediada paylaş, ya da tədbir təşkil edənlərin diqqətini cəlb etmək üçün ictimai profil keçidini kopyala. | Step 4 description |
| onboard.step4.cta | Done | Hazır | Final CTA button |
| onboard.skipAnytime | You can always do this later. | Siz bunu istənilən vaxt sonradan edə bilərsiniz. | Small text, skip option |

---

## 4. Assessment

**Start Assessment Screen**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| assess.hero | Ready to discover your AURA score? | AURA xalınızı kəşf etməyə hazırsınız? | Hero CTA text |
| assess.timeEstimate | Takes about 10–15 minutes | Təxminən 10–15 dəqiqə çəkir | Subtitle |
| assess.startButton | Start Assessment | Qiymətləndirməni Başlat | CTA button |
| assess.reviewButton | Review Your AURA | AURA-nı Nəzərdən Keçir | Alt button if already completed |
| assess.offline | Your answers are saved locally and will sync when you're back online. | Sizin cavablarınız yerli olaraq saxlanılır və siz onlayn olduqda sinxronizasiya olunacaq. | Offline notice |

**Question Navigation**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| assess.questionCounter | Question {n} of {total} | Sual {n} {total} | Question progress counter |
| assess.timeRemaining | Time remaining: {time} | Qalan vaxt: {time} | Timer display |
| assess.questionsLeft | {n} question{plural} left | {n} sual qalıb | Questions remaining |
| assess.previousButton | Previous | Əvvəlki | Back button |
| assess.nextButton | Next | Sonrakı | Forward button |
| assess.skipButton | Skip | Keçmək | Skip question (if allowed) |
| assess.submitButton | Submit Assessment | Qiymətləndirməni Təqdim et | Final submit button |

**Question Types**

**BARS Scale (Behaviorally Anchored Rating Scale)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| assess.barsLabel | Rate your agreement on the scale below | Aşağıdakı tərəzidə razılığınızı qiymətləndirin | BARS prompt |
| assess.barsScale.1 | Strongly Disagree | Ciddi Olaraq Razı Deyiləm | Level 1 anchor |
| assess.barsScale.2 | Disagree | Razı Deyiləm | Level 2 anchor |
| assess.barsScale.3 | Somewhat Disagree | Bir Qədər Razı Deyiləm | Level 3 anchor |
| assess.barsScale.4 | Neutral | Neytral | Level 4 anchor |
| assess.barsScale.5 | Somewhat Agree | Bir Qədər Razı Oluyam | Level 5 anchor |
| assess.barsScale.6 | Agree | Razı Oluyam | Level 6 anchor |
| assess.barsScale.7 | Strongly Agree | Ciddi Olaraq Razı Oluyam | Level 7 anchor |

**Multiple Choice**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| assess.mcqLabel | Select the best answer | Ən yaxşı cavabı seçin | MCQ instruction |
| assess.selectOption | Select one | Birini seçin | Placeholder for choice |

**Open-Ended Text**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| assess.openTextLabel | Describe your approach in detail | Sizin yanaşmanızı ətraflı şəkildə təsvir edin | Text input label |
| assess.openTextPlaceholder | Write your response here... | Cavabınızı burada yazın... | Text input placeholder |
| assess.characterCount | {n} / 500 characters | {n} / 500 simvol | Character counter |

**Progress & Saving**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| assess.progressBar | {percentage}% complete | {percentage}% tamamlanmış | Progress bar label |
| assess.savingLocally | Saving locally... | Yerli olaraq saxlanılır... | Auto-save indicator |
| assess.savedLocally | Answers saved locally ✓ | Cavablar yerli olaraq saxlanılır ✓ | Saved confirmation |
| assess.syncPending | Will sync when online | İnternete bağlandıqda sinxronizasiya olunacaq | Offline sync status |

**Completion**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| assess.completeTitle | Assessment Complete! | Qiymətləndirmə Tamamlandı! | Success title |
| assess.calculating | Calculating your AURA score... | AURA xalınız hesablanır... | Processing state |
| assess.evaluating | Evaluating your responses with AI... | Cavablarınız süni intellekt ilə qiymətləndirilir... | AI evaluation status |
| assess.thankYou | Thank you for completing your assessment! | Qiymətləndirməni tamamladığınız üçün təşəkkür edirik! | Gratitude message |
| assess.viewResults | View Your Results | Nəticələrinizi Görün | CTA to results page |

---

## 5. AURA Score & Results

**Score Reveal**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| results.yourScore | Your AURA Score | Sizin AURA Xalınız | Section title |
| results.scoreValue | {score} / 100 | {score} / 100 | Numeric score display |
| results.congratulations | Congratulations! | Təbrik edirik! | Celebration message (varies by tier) |

**Badge Tier Messages**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| results.badge.platinum | You've achieved Platinum status. You're an exemplary volunteer ready for any challenge. | Siz Platin statusuna çatmısınız. Siz istənilən çətinliyə hazır nümunəvi könüllüsünüz. | Platinum badge copy |
| results.badge.gold | You've earned a Gold badge. You're a highly skilled and reliable volunteer. | Siz Qızıl nişan qazanmısınız. Siz yüksək bacarıqlı və etibarlı könüllüsünüz. | Gold badge copy |
| results.badge.silver | You've received a Silver badge. You have solid volunteer skills and are ready to grow. | Siz Gümüş nişan almısınız. Sizin sağlam könüllü bacarıqlarınız var və böyümək üçün hazırsınız. | Silver badge copy |
| results.badge.bronze | You've earned a Bronze badge. This is your start to becoming an amazing volunteer. | Siz Brons nişan qazanmısınız. Bu, məharətli könüllü olmağa doğru sizin başlanğıcınızdır. | Bronze badge copy |
| results.badge.none | Keep growing. Retake the assessment in 30 days to improve your score. | Böyümək davam et. Xalını yaxşılaşdırmaq üçün 30 gündən sonra qiymətləndirmə yenidən keçin. | None badge copy |

**Competency Labels (8 Total)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| competency.communication | Communication | Kommunikasiya | Competency 1 (20% weight) |
| competency.reliability | Reliability | Etibarlılıq | Competency 2 (15% weight) |
| competency.english_proficiency | English Proficiency | İngilis Dili Bilgisi | Competency 3 (15% weight) |
| competency.leadership | Leadership | Liderlik | Competency 4 (15% weight) |
| competency.event_performance | Event Performance | Tədbir Performansı | Competency 5 (10% weight) |
| competency.tech_literacy | Tech Literacy | Texniki Savadlılıq | Competency 6 (10% weight) |
| competency.adaptability | Adaptability | Uyğunlaşdırılabilirlik | Competency 7 (10% weight) |
| competency.empathy_safeguarding | Empathy & Safeguarding | Empati & Qorunma | Competency 8 (5% weight) |

**Competency Description Examples**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| competency.communication.desc | Your ability to express ideas clearly and listen actively | Fikirlərini aydın şəkildə ifadə etmə və aktiv dinləmə bacarığı | Communication descriptor |
| competency.reliability.desc | Your consistency, dependability, and follow-through | Sizin ardıcıllığınız, etibarlılığınız və tamamlama | Reliability descriptor |
| competency.english_proficiency.desc | Your fluency and effectiveness in spoken and written English | İngilis dilində danışıqda və yazısında faydalılığınız | English proficiency descriptor |
| competency.leadership.desc | Your ability to guide, motivate, and make decisions | Bələdçilik etmə, motivasiya etmə və qərar qəbul etmə bacarığı | Leadership descriptor |
| competency.event_performance.desc | Your effectiveness in event execution and collaboration | Tədbir icrasında və əməkdaşlıqda effektivliyiniz | Event performance descriptor |
| competency.tech_literacy.desc | Your comfort with digital tools and technology adoption | Rəqəmsal alətlər ilə rahatınız və texnologiya qəbulu | Tech literacy descriptor |
| competency.adaptability.desc | Your flexibility and resilience in changing environments | Dəyişən mühitlərdə elastikliyiniz və sərçılıqınız | Adaptability descriptor |
| competency.empathy_safeguarding.desc | Your compassion for others and commitment to safe practices | Başqaları üçün şəfqəti və təhlükəsiz praktikalara bağlılığı | Empathy descriptor |

**Reassessment**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| results.retakeInfo | You can retake your assessment once every 30 days | Hər 30 gündən bir qiymətləndirmə yenidən keçə bilərsiniz | Retake rule info |
| results.nextRetake | Available in {days} days | {days} gündən sonra mövcuddur | Countdown to next retake |
| results.retakeButton | Retake Assessment | Qiymətləndirmə Yenidən Keçin | CTA button |
| results.shareButton | Share Your Badge | Nişanınızı Paylaş | Share CTA button |
| results.downloadButton | Download Certificate | Sertifikatı Yükləyin | Download CTA button (if available) |

---

## 6. Profile

**Profile Overview**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| profile.myProfile | My Profile | Mənim Profilim | Page title |
| profile.publicProfile | Public Profile | İctimai Profil | View public profile link |
| profile.editProfile | Edit Profile | Profili Düzəlt | Edit mode button |
| profile.saveChanges | Save Changes | Dəyişiklikləri Saxla | Save button |
| profile.cancelEdit | Cancel | Ləğv et | Cancel button |
| profile.shareProfile | Share Your Profile | Profilini Paylaş | Share CTA |
| profile.copyLink | Copy Link | Keçidi Kopyala | Copy profile URL button |
| profile.linkCopied | Link copied to clipboard | Keçid buferə kopyalanmışdır | Toast confirmation |

**Profile Fields**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| profile.firstName | First Name | Ad | Text input |
| profile.lastName | Last Name | Soyad | Text input |
| profile.email | Email Address | E-poçt Ünvanı | Display/input |
| profile.phone | Phone (optional) | Telefon (optional) | Text input |
| profile.bio | Bio | Bioqrafiya | Text area for personal bio |
| profile.bioPlaceholder | Tell us about yourself... | Özündən bizə söylə... | Text area placeholder |
| profile.location | Location | Yerləşməsi | City/region dropdown |
| profile.skills | Skills (from assessment) | Bacarıqlar (qiymətləndirmədən) | Display only |
| profile.interests | Interests | Maraqlar | Multi-select or tags |
| profile.languages | Languages | Dillər | Multi-select (AZ, EN, RU, TR) |
| profile.availability | Availability | Mövcudluq | Dropdown (weekends, evenings, flexible) |

**Verification Badges**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| profile.verification.selfAssessed | Self-Assessed | Özü qiymətləndirilmiş | Badge label |
| profile.verification.orgVerified | Organization Verified | Təşkilat tərəfindən Təsdiqlənmişdir | Badge label |
| profile.verification.peerVerified | Peer Verified | Həmyaşıd tərəfindən Təsdiqlənmişdir | Badge label |
| profile.verifyTooltip | This volunteer's competencies have been verified by {source} | Bu könüllünün bacarıqları {source} tərəfindən təsdiq edilmişdir | Tooltip on hover |

**Empty State (No Assessment)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| profile.noScore.title | Complete Your Assessment | Qiymətləndirməni Tamamla | Empty state title |
| profile.noScore.desc | Take the AURA assessment to unlock your verified profile and discover opportunities. | AURA qiymətləndirməsini keçin, təsdiqlənmiş profilinizi açın və imkanları kəşf edin. | Empty state description |
| profile.noScore.cta | Start Assessment | Qiymətləndirmə Başlat | CTA button |

---

## 7. Events

**Event Listing**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| events.title | Events | Tədbirlər | Page title |
| events.filter.all | All Events | Bütün Tədbirlər | Filter tab |
| events.filter.my | My Events | Mənim Tədbirlərim | Registered events tab |
| events.filter.upcoming | Upcoming | Gələcəkdə | Upcoming events tab |
| events.filter.past | Past | Keçmiş | Past events tab |
| events.filterButton | Filter | Filtr | Open filter panel |
| events.sortButton | Sort | Sıralama | Sort options dropdown |
| events.searchPlaceholder | Search events... | Tədbirləri axtarın... | Search input placeholder |

**Event Card**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| events.card.register | Register | Qeydiyyatdan Keç | CTA button (unregistered) |
| events.card.registered | Registered ✓ | Qeydiyyatdan Keçdi ✓ | Button state (registered) |
| events.card.spotsLeft | Spots left: {n} | Qalan yerlər: {n} | Availability badge |
| events.card.fullCapacity | Event Full | Tədbir Dolu | Disabled state message |
| events.card.requiresBadge | Requires {tier}+ badge | {tier}+ nişan tələb olunur | AURA requirement |
| events.card.unlockBadge | Unlock this tier to register | Bu səviyyəni açmaq üçün qeydiyyatdan keçin | Tooltip for insufficient tier |
| events.card.date | {date} | {date} | Event date display |
| events.card.location | {location} | {location} | Event location |
| events.card.viewDetails | View Details | Ətraflı Bax | Link to event detail page |

**Event Detail Page**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| events.detail.title | Event Details | Tədbir Məlumatları | Page title |
| events.detail.description | Description | Təsvir | Section header |
| events.detail.date | Date & Time | Tarix və Saat | Info label |
| events.detail.location | Location | Yerləşməsi | Info label |
| events.detail.organizer | Organized by | {organizerName} tərəfindən təşkil edilir | Organizer credit |
| events.detail.volunteer_count | {n} volunteers attending | {n} könüllü iştirak edir | Attendance count |
| events.detail.requirementsTitle | Requirements | Tələblər | Section header |
| events.detail.minBadge | Minimum Badge | Minimum Nişan | Requirement label |
| events.detail.skills | Skills | Bacarıqlar | Requirement label |
| events.detail.registerButton | Register for Event | Tədbir Üçün Qeydiyyatdan Keçin | CTA button |

**Empty State (No Events)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| events.empty.title | No Events Available | Tədbir Mövcud Deyil | Empty state title |
| events.empty.desc | Check back soon for upcoming opportunities. | Tezliklə yeni imkanlar üçün yenidən yoxlayın. | Empty state description |
| events.empty.cta | Explore Other Features | Digər Xüsusiyyətləri Kəşf Edin | Alt CTA |

---

## 8. Organization Dashboard

**Organization Overview**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| org.dashboard | Organization Dashboard | Təşkilat Paneli | Page title |
| org.activeEvents | Active Events | Aktiv Tədbirlər | Widget title |
| org.volunteerCount | {n} volunteers registered | {n} könüllü qeydiyyatdan keçdi | Stat display |
| org.createEvent | Create Event | Tədbir Yarat | CTA button |
| org.manageEvents | Manage Events | Tədbirləri İdarə Et | Link/button |

**Volunteer Search & Filter**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| org.searchVolunteers | Search volunteers by competency | Bacarıqla könüllüləri axtarın | Search input label |
| org.filterByTier | Filter by badge tier | Nişan səviyyəsi ilə filtr et | Filter label |
| org.filterBySkill | Filter by skill | Bacarıq ilə filtr et | Filter label |
| org.sortBy | Sort by | Sırala: | Dropdown label |
| org.sortOption.scoreHighToLow | Score (High to Low) | Xal (Yüksəkdən Aşağıya) | Sort option |
| org.sortOption.recent | Most Recent | Ən Son | Sort option |
| org.sortOption.availability | Availability | Mövcudluq | Sort option |

**Volunteer Card (in Org Dashboard)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| org.volunteerCard.score | AURA: {score} | AURA: {score} | Score badge |
| org.volunteerCard.tier | {tier} Badge | {tier} Nişan | Badge tier label |
| org.volunteerCard.competencies | Top competencies | Əsas Bacarıqlar | Section label |
| org.volunteerCard.attest | Attest Competencies | Bacarıqları Təsdiq Et | CTA button |
| org.volunteerCard.rate | Rate Performance | Performansı Qiymətləndirin | CTA button |
| org.volunteerCard.viewProfile | View Full Profile | Tam Profili Bax | Link |

**Attestation Modal**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| org.attestation.title | Attest Volunteer Competencies | Könüllü Bacarıqlarını Təsdiq Et | Modal title |
| org.attestation.instructions | Select which competencies you've observed this volunteer demonstrate in your organization. | Bu könüllünün təşkilatınızda nə bacarıqları göstərdiyi müşahidə etdiyinizi seçin. | Modal instructions |
| org.attestation.selectAll | Select All | Hamısını Seçin | Checkbox |
| org.attestation.confirmButton | Submit Attestation | Attestasiyanı Təqdim Et | CTA button |
| org.attestation.cancelButton | Cancel | Ləğv Et | Cancel button |
| org.attestation.success | Thank you! Your attestation has been recorded. | Təşəkkür! Sizin attestasiyalarınız qeyd olunmuşdur. | Success toast |

**Performance Rating Modal**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| org.rating.title | Rate Volunteer Performance | Könüllü Performansını Qiymətləndirin | Modal title |
| org.rating.scale | Rate from 1 (poor) to 5 (excellent) | 1-dən (zəif) 5-ə (mükəmməl) qiymətləndirin | Scale instruction |
| org.rating.comment | Additional Feedback (optional) | Əlavə Rəy (istəkli) | Comment field label |
| org.rating.submitButton | Submit Rating | Reytinqi Təqdim Et | CTA button |
| org.rating.success | Thank you for your feedback! | Rəy üçün təşəkkür! | Success toast |

---

## 9. Notifications

**Notification Center**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| notif.title | Notifications | Bildirişlər | Page title |
| notif.markAllRead | Mark all as read | Hamısını oxunmuş kimi işarələ | Link/button |
| notif.clearAll | Clear all | Hamısını Sil | Link/button |
| notif.empty | You're all caught up! | Sən tamamilə tutduğun! | Empty state message |
| notif.noNew | No new notifications | Yeni bildirişlər yoxdur | Empty state message |

**Notification Types**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| notif.scoreReady.title | Your AURA score is ready! | Sizin AURA xalınız hazırdır! | Notification title |
| notif.scoreReady.body | Tap to view your results and unlocked opportunities. | Nəticələrinizi və açılmış imkanlarını görmək üçün toxunun. | Notification body |
| notif.eventReminder.title | Upcoming: {eventName} | Gələcəkdə: {eventName} | Notification title |
| notif.eventReminder.body | Your event starts in 24 hours. See you there! | Sizin tədbir 24 saat ərzində başlayır. Orada sən görəcəyik! | Notification body |
| notif.orgAttestation.title | {orgName} has attested your skills | {orgName} sizin bacarıqlarınızı təsdiq etmişdir | Notification title |
| notif.orgAttestation.body | View your updated profile with verified competencies. | Təsdiqlənmiş bacarıqlarla yeniləşdirilmiş profilinizi görün. | Notification body |
| notif.peerRequest.title | {peerName} wants to verify your competencies | {peerName} sizin bacarıqlarınızı doğrulamaq istəyir | Notification title |
| notif.peerRequest.body | Tap to review and accept or decline the request. | Sorğunu nəzərdən keçirmək və qəbul etmək və ya rədd etmək üçün toxunun. | Notification body |
| notif.badgeChange.title | Your badge tier has changed | Sizin nişan səviyyəniz dəyişmişdir | Notification title |
| notif.badgeChange.body | Congratulations! You've been upgraded to {tier}. | Təbriklər! Siz {tier}-ə yüksəldilmisiniz. | Notification body |
| notif.welcome.title | Welcome to Volaura! | Volaura-ya xoş gəlmisiniz! | Notification title |
| notif.welcome.body | Complete your profile to get started. | Başlamaq üçün profilinizi tamamlayın. | Notification body |

---

## 10. Error Messages

**Network & Connectivity**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| errors.noConnection | Connection lost. Your progress is saved. | Bağlantı kəsildi. Sizin tərəqqi saxlanılmışdır. | Offline error |
| errors.noConnectionSubtext | We'll sync when you're back online. | Siz onlayn olduqda sinxronizasiya edəcəyik. | Offline help text |
| errors.slowConnection | Slow connection detected. Some features may take longer. | Yavaş bağlantı aşkar edildi. Bəzi xüsusiyyətlər daha uzun çəkə bilər. | Slow connection warning |
| errors.reconnecting | Reconnecting... | Yenidən bağlanılır... | Reconnection status |
| errors.retry | Retry | Yenidən cəhd edin | Retry button |

**Authentication Errors**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| errors.invalidOrExpired | Invalid or expired link | Etibarsız və ya sona çatmış keçid | Generic auth error |
| errors.sessionExpired | Your session has expired. Please log in again. | Sizin sessiya sona çatmışdır. Zəhmət olmasa yenidən daxil olun. | Session timeout error |
| errors.accountNotFound | Account not found. Please sign up. | Hesab tapılmadı. Zəhmət olmasa qeydiyyatdan keçin. | Account lookup error |
| errors.tooManyAttempts | Too many attempts. Try again in {minutes} minutes. | Çox çox cəhd edin. {minutes} dəqiqədən sonra cəhd edin. | Rate limit error |
| errors.accountLocked | Your account is temporarily locked. Contact support. | Sizin hesab müvəqqəti olaraq kilidlənib. Dəstəklə əlaqə saxlayın. | Account lockout error |

**Validation Errors**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| errors.required | This field is required | Bu sahə tələb olunur | Generic required field |
| errors.invalidEmail | Please enter a valid email address | Zəhmət olmasa düzgün e-poçt ünvanı daxil edin | Email validation |
| errors.passwordTooShort | Password must be at least 8 characters | Şifrə ən az 8 simvol olmalıdır | Password validation |
| errors.passwordMismatch | Passwords do not match | Şifrələr uyğun gəlmir | Password confirmation error |
| errors.invalidPhone | Please enter a valid phone number | Zəhmət olmasa düzgün telefon nömrəsi daxil edin | Phone validation |
| errors.bioTooLong | Bio must be less than 500 characters | Bioqrafiya 500 simvoldan az olmalıdır | Bio length error |
| errors.selectOption | Please select an option | Zəhmət olmasa bir seçim seçin | Dropdown required |
| errors.selectAtLeastOne | Please select at least one item | Zəhmət olmasa ən az bir element seçin | Multi-select required |

**Assessment-Specific Errors**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| errors.assessmentNotFound | Assessment not found | Qiymətləndirmə tapılmadı | Assessment lookup error |
| errors.alreadyAssessed | You've already completed an assessment today | Siz artıq bu gün qiymətləndirmə tamamladınız | Duplicate assessment attempt |
| errors.cannotRetake | You can retake this assessment in {days} days | Bu qiymətləndirmə yenidən keçə bilərsiniz {days} gündən sonra | Retake cooldown error |
| errors.questionFailed | Could not load question. Please try again. | Sual yükləmə alınmadı. Zəhmət olmasa yenidən cəhd edin. | Question loading error |
| errors.submitFailed | Failed to submit assessment. Please try again. | Qiymətləndirmə təqdim etmə uğursuz oldu. Zəhmət olmasa yenidən cəhd edin. | Submission error |
| errors.evaluationFailed | Could not evaluate your responses. Please try again later. | Cavablarınız qiymətləndirilə bilmədi. Zəhmət olmasa sonra yenidən cəhd edin. | Evaluation error (LLM failure) |

**Event Registration Errors**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| errors.eventFull | This event is at capacity. Check back soon. | Bu tədbir kapasitededir. Tezliklə yenidən yoxlayın. | Event full error |
| errors.lowBadge | You don't meet the minimum badge requirement. | Siz minimum nişan tələbini yerinə yetirməyirsiniz. | Badge requirement error |
| errors.alreadyRegistered | You're already registered for this event | Siz artıq bu tədbir üçün qeydiyyatdan keçmisiniz | Duplicate registration error |
| errors.eventNotFound | Event not found | Tədbir tapılmadı | Event lookup error |
| errors.registrationFailed | Registration failed. Please try again. | Qeydiyyat uğursuz oldu. Zəhmət olmasa yenidən cəhd edin. | Generic registration error |

**Generic Errors**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| errors.generic | Something went wrong. Please try again. | Bir şey yanlış getdi. Zəhmət olmasa yenidən cəhd edin. | Catch-all error |
| errors.serverError | Server error. Our team has been notified. | Server xətası. Komandamız xəbərdar edilmişdir. | 500 error |
| errors.notFound | Page not found | Səhifə tapılmadı | 404 error |
| errors.unauthorized | You don't have permission to access this | Buna girmək üçün icazəniz yoxdur | 403 error |
| errors.tryAgain | Try again | Yenidən cəhd edin | Generic retry button |
| errors.contactSupport | Contact Support | Dəstəklə əlaqə saxlayın | Support link |

---

## 11. Empty States

**No Assessments Taken**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| empty.noAssessments.title | Take Your First Assessment | İlk Qiymətləndirmənizi Keçin | Empty state title |
| empty.noAssessments.desc | Unlock your AURA score and discover verified opportunities. | AURA xalını açın və təsdiqlənmiş imkanları kəşf edin. | Empty state description |
| empty.noAssessments.cta | Start Assessment | Qiymətləndirmə Başlat | CTA button |

**No Events Available**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| empty.noEvents.title | No Events Available | Tədbir Mövcud Deyil | Empty state title |
| empty.noEvents.desc | Check back soon for exciting opportunities in your area. | Sizin ərazinizdə maraqlı imkanlar üçün tezliklə yenidən yoxlayın. | Empty state description |
| empty.noEvents.cta | Browse Categories | Kateqoriyalara Bax | Alt CTA (future feature) |

**No Notifications**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| empty.noNotifications.title | You're All Caught Up | Sən tamamilə tutduğun | Empty state title |
| empty.noNotifications.desc | No new notifications at this time. | Bu zaman yeni bildirişlər yoxdur. | Empty state description |

**No Registered Events**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| empty.noRegistered.title | You Haven't Registered Yet | Hələ Qeydiyyatdan Keçməmisiniz | Empty state title |
| empty.noRegistered.desc | Find and register for events that match your skills. | Bacarıqlarınıza uyğun tədbirləri tapın və qeydiyyatdan keçin. | Empty state description |
| empty.noRegistered.cta | Browse Events | Tədbirə Bax | CTA button |

**Organization: No Volunteers**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| empty.noVolunteers.title | No Volunteers Yet | Hələ Könüllü Yoxdur | Empty state title |
| empty.noVolunteers.desc | Create an event to start attracting verified participants. | Təsdiqlənmiş iştirakçıları cəlb etməyə başlamaq üçün tədbir yaradın. | Empty state description |
| empty.noVolunteers.cta | Create First Event | İlk Tədbirini Yarat | CTA button |

---

## 12. CTAs & Buttons

**Primary Actions (High Priority)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| cta.startAssessment | Start Assessment | Qiymətləndirmə Başlat | Primary button, hero sections |
| cta.shareBadge | Share Your Badge | Nişanınızı Paylaş | Primary button, results page |
| cta.registerEvent | Register for Event | Tədbir Üçün Qeydiyyatdan Keçin | Primary button, event cards |
| cta.createEvent | Create Event | Tədbir Yarat | Primary button, org dashboard |
| cta.submitAssessment | Submit Assessment | Qiymətləndirməni Təqdim Et | Primary button, assessment end |
| cta.updateProfile | Update Profile | Profili Yeniləyin | Primary button, profile edit |
| cta.sendEmail | Send Magic Link | Sehrli Keçidi Göndər | Primary button, auth flow |
| cta.continue | Continue | Davam etmək | Primary button, modals |

**Secondary Actions (Lower Priority)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| cta.viewDetails | View Details | Ətraflı Bax | Secondary button |
| cta.learnMore | Learn More | Daha Çox Öyrən | Secondary button |
| cta.editProfile | Edit Profile | Profili Düzəlt | Secondary button |
| cta.viewResults | View Your Results | Nəticələrinizi Görün | Secondary button |
| cta.cancel | Cancel | Ləğv et | Cancel button |
| cta.back | Back | Geri | Back button |
| cta.next | Next | Sonrakı | Navigation button |
| cta.previous | Previous | Əvvəlki | Navigation button |
| cta.skip | Skip | Keçmək | Optional action button |
| cta.close | Close | Bağla | Close button |

**Destructive Actions (Warning)**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| cta.delete | Delete | Sil | Destructive button (red) |
| cta.deleteAccount | Delete Account | Hesabı Sil | Destructive button (red) |
| cta.cancelRegistration | Cancel Registration | Qeydiyyatı Ləğv Et | Destructive button (red) |
| cta.unregister | Unregister | Qeydiyyatdan Keç | Destructive button (red) |
| cta.confirm | Confirm | Təsdiq Et | Confirmation button (red for destructive) |

**Button States**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| button.loading | Loading... | Yüklənir... | Disabled state |
| button.disabled | Disabled | Deaktiv | Disabled state |
| button.submitting | Submitting... | Təqdim Edilir... | Form submission state |
| button.retrying | Retrying... | Yenidən Cəhd Edilidir... | Retry state |

---

## 13. Toasts & Confirmations

**Success Toasts**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| toast.profileUpdated | Profile updated successfully | Profil uğurla yəniləşdirildi | Success confirmation |
| toast.eventRegistered | You've registered for the event | Siz tədbir üçün qeydiyyatdan keçmisiniz | Registration success |
| toast.linkCopied | Link copied to clipboard | Keçid buferə kopyalanmışdır | Clipboard confirmation |
| toast.assessmentSaved | Assessment saved locally | Qiymətləndirmə yerli olaraq saxlanılmışdır | Offline save confirmation |
| toast.settingsSaved | Settings saved | Ayarlar saxlanıldı | Settings save confirmation |
| toast.badgeShared | Badge shared! | Nişan paylaşıldı! | Share success |

**Error Toasts**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| toast.errorSaving | Could not save changes | Dəyişikliklər saxlana bilmədi | Generic save error |
| toast.errorRegistering | Could not register for event | Tədbir üçün qeydiyyatdan keçilə bilmədi | Registration error |
| toast.errorLoading | Could not load data | Məlumatlar yüklənə bilmədi | Loading error |
| toast.errorUploadingImage | Could not upload image | Şəkil yükləmə alınmadı | Image upload error |
| toast.networkError | Network error. Please try again. | Şəbəkə xətası. Zəhmət olmasa yenidən cəhd edin. | Network error |

**Info Toasts**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| toast.processing | Processing... | Hazırlanır... | Loading state |
| toast.checkEmail | Check your email | E-poçtunuzu yoxlayın | Reminder to check email |
| toast.willSyncOnline | Will sync when online | Onlayn olduqda sinxronizasiya olunacaq | Offline sync info |
| toast.offlineMode | You're offline | Siz oflayndasınız | Offline mode indicator |

**Confirmation Dialogs**

| Key | EN | AZ | Notes |
|-----|----|----|-------|
| confirm.deleteAccount.title | Delete Your Account? | Hesabınızı Silmək İstəyirsiniz? | Dialog title |
| confirm.deleteAccount.body | This action cannot be undone. All your data will be permanently deleted. | Bu əməl geri alına bilməz. Bütün məlumatlarınız qalıcı olaraq silinəcəkdir. | Dialog body |
| confirm.deleteAccount.confirm | Yes, Delete My Account | Bəli, Hesabımı Sil | Confirmation button |
| confirm.deleteAccount.cancel | Cancel | Ləğv et | Cancel button |
| confirm.cancelRegistration.title | Cancel Event Registration? | Tədbir Qeydiyyatını Ləğv Etmək İstəyirsiniz? | Dialog title |
| confirm.cancelRegistration.body | You will lose your spot. Are you sure? | Sizin yerini itirəcəksiniz. Əminsiniz? | Dialog body |
| confirm.cancelRegistration.confirm | Yes, Cancel Registration | Bəli, Qeydiyyatı Ləğv Et | Confirmation button |
| confirm.cancelRegistration.cancel | Keep My Registration | Qeydiyyatımı Saxla | Cancel button |

---

## Implementation Checklist

- [ ] All keys follow `namespace.feature.element` pattern
- [ ] Azerbaijani text uses formal "Siz" throughout
- [ ] Azerbaijani text includes special characters: ə, ğ, ı, ö, ü, ş, ç
- [ ] English text uses American English spelling
- [ ] Sentences are concise (max 15 words for mobile screens)
- [ ] All placeholders use `{variable}` format
- [ ] Buttons use imperative verbs (Start, Share, Register, not Starting, Sharing)
- [ ] Empty states include both title and CTA
- [ ] Error messages are specific, not generic
- [ ] Toast messages are under 10 words
- [ ] Links to [[ANIMATION-SYSTEM.md]] for transition states
- [ ] Translation files created in `public/locales/az/` and `public/locales/en/`
- [ ] All strings use `i18n.t()` in code, not hardcoded
- [ ] Tested in both mobile and desktop viewports
- [ ] Reviewed by AZ native speaker for tone and accuracy

---

## Related Documentation

- [[../ANIMATION-SYSTEM.md]] — micro-interaction copy pairing (e.g., button press confirmation, toast animations)
- [[../../CLAUDE.md]] — global project rules (i18n namespacing, tech stack)
- [[../DECISIONS.md]] — rationale for copy choices and brand voice
- `public/locales/{locale}/{namespace}.json` — actual translation files (generated from this reference)

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-03-22 | Design System | Initial comprehensive catalog v1.0 |


