import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

/**
 * Terms of Service v2 — 2026-05-01 effective
 *
 * Source: GPT-5 generated 2026-04-26, courier-delivered by CEO.
 * Cross-referenced against GDPR (EUR-Lex CELEX 32016R0679),
 * Azerbaijan Law on Personal Data, Delaware General Corporation Law.
 *
 * Bilingual inline JSX (AZ + EN). Locale-conditional rendering.
 * Replaces stub i18n keys (terms.s1..s7) — keys retained in
 * common.json for backward compat but no longer read here.
 *
 * Canonical AZ + EN markdown source: for-ceo/legal/terms-2026-05-01.md
 */
export const metadata: Metadata = {
  title: "Terms of Service — Volaura",
};

export default async function TermsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const isAz = locale === "az";

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b border-white/10 bg-surface-container/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link
            href={`/${locale}`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {isAz ? "Volaura-ya qayıt" : "Back to Volaura"}
          </Link>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-bold font-headline mb-2">
            {isAz ? "İstifadə Şərtləri" : "Terms of Service"}
          </h1>
          <p className="text-muted-foreground text-sm">
            {isAz ? "Qüvvəyə minmə tarixi: 1 may 2026" : "Effective date: 2026-05-01"}
          </p>
        </div>

        <div className="prose prose-invert prose-sm max-w-none space-y-8 text-sm leading-relaxed text-muted-foreground">
          {isAz ? <TermsAz /> : <TermsEn />}
        </div>

        <div className="mt-16 pt-8 border-t border-white/10 text-center text-xs text-muted-foreground">
          <p>
            © 2026 VOLAURA, Inc. ·{" "}
            <Link href={`/${locale}/privacy`} className="hover:text-foreground transition-colors">
              {isAz ? "Məxfilik Siyasəti" : "Privacy Policy"}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

/* ──────────────────────────  AZ  ────────────────────────── */
function TermsAz() {
  return (
    <>
      <Section title="1. Giriş">
        <p>
          Bu Xidmət Şərtləri VOLAURA, Inc. və VOLAURA platformasından istifadənizi tənzimləyir. VOLAURA, Inc. Delaware ştatında qeydiyyatdan keçmiş C-Corporation-dır. VOLAURA-dan istifadə etməklə bu Şərtlərlə razılaşırsınız. Əlaqə: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>

      <Section title="2. Xidmət nədir">
        <p>
          VOLAURA peşəkar bacarıqların qiymətləndirilməsi, nəticələrin göstərilməsi və verified professional talent profiling üçün platformadır. Biz iş, gəlir, qəbul, sertifikat və ya istənilən konkret nəticəni zəmanət vermirik.
        </p>
      </Section>

      <Section title="3. Yaş məhdudiyyəti">
        <p>
          VOLAURA yalnız <strong className="text-foreground">18 yaş və yuxarı</strong> şəxslər üçündür. 18 yaşdan aşağısınızsa, xidmətdən istifadə etməyin.
        </p>
      </Section>

      <Section title="4. Hesab">
        <p>
          Hesab yaradanda doğru məlumat verməlisiniz, hesabınızı qorumağa kömək etməlisiniz, hesabınızla baş verən fəaliyyətə görə məsuliyyət daşıyırsınız. Google ilə giriş edirsinizsə, Google hesabınızı da təhlükəsiz saxlamalısınız.
        </p>
      </Section>

      <Section title="5. Assesment və platformadan istifadə">
        <p>
          Siz razılaşırsınız ki: assesmentləri dürüst cavablayacaqsınız, başqasının adından istifadə etməyəcəksiniz, sistemi aldatmağa, manipulyasiya etməyə və ya saxta nəticə yaratmağa çalışmayacaqsınız, platformanı yalnız qanuni məqsədlərlə istifadə edəcəksiniz. Biz saxtakarlıq, abuse və təhlükəsizlik risklərini aşkar etmək üçün yoxlamalar apara bilərik.
        </p>
      </Section>

      <Section title="6. Sizin kontentiniz">
        <p>
          Siz platformaya məlumat, cavab, profil mətni və opsional foto yükləyə bilərsiniz. Siz öz kontentinizə sahib olaraq qalırsınız. Amma xidməti işlətmək üçün bizə həmin kontenti saxlamaq, emal etmək, göstərmək, təhlükəsizlik və support məqsədləri ilə istifadə etmək üçün məhdud hüquq verirsiniz. Əgər opsional foto yükləyirsinizsə, onun üçün hüququnuz olmalıdır.
        </p>
      </Section>

      <Section title="7. AI və avtomatlaşdırılmış qiymətləndirmə">
        <p>
          VOLAURA assesment cavablarını və digər siqnalları AI və qayda əsaslı sistemlərlə emal edə bilər. Bu sistemlər skor, insight, tövsiyə, uyğunluq siqnalı yarada bilər. AI nəticələri faydalıdır, amma səhvsiz deyil. Siz və platformadan istifadə edən digər tərəflər bu nəticələri yeganə qərar mənbəyi kimi istifadə etməməlisiniz. VOLAURA özü sizin barənizdə təkbaşına hüquqi qüvvəli qərar çıxarmağa yönəlməyib. Əgər belə emal sizə ciddi təsir göstərirsə, siz əlavə izah və insan baxışı istəyə bilərsiniz.
        </p>
      </Section>

      <Section title="8. Ödənişlər">
        <p>
          Əgər ödənişli funksiya və ya abunə aktiv edilərsə: ödənişlər Stripe vasitəsilə işlənir, siz düzgün billing məlumatı verməlisiniz, qiymət, renewal və refund şərtləri həmin plan təqdim olunanda göstəriləcək, Stripe öz şərt və siyasətlərini ayrıca tətbiq edə bilər. Biz kart məlumatlarını saxlamırıq.
        </p>
      </Section>

      <Section title="9. Qadağan olunan istifadələr">
        <p>
          Aşağıdakılar qadağandır: başqasının hesabına icazəsiz giriş, platformanı reverse-engineer etmək və ya zədələmək, spam, scraping və ya avtomatlaşdırılmış abuse, zərərli kod yükləmək, saxta profil, saxta assesment və ya saxta sübut yaratmaq, qanunu və üçüncü şəxslərin hüquqlarını pozmaq.
        </p>
      </Section>

      <Section title="10. Hesabın dayandırılması və ya bağlanması">
        <p>
          Bu Şərtləri pozsanız və ya platforma üçün risk yaratsanız, biz hesabınızı məhdudlaşdıra, dayandıra və ya bağlaya bilərik. Siz də istənilən vaxt hesabınızı bağlamağı xahiş edə bilərsiniz.
        </p>
      </Section>

      <Section title="11. Məxfilik">
        <p>
          Şəxsi məlumatların necə işlənməsi bizim Privacy Policy sənədimizdə izah olunur. VOLAURA-dan istifadə etməklə həmin siyasətin də sizə tətbiq olacağını qəbul edirsiniz.
        </p>
      </Section>

      <Section title="12. Intellectual property">
        <p>
          Platformanın özü — dizayn, mətn, proqram kodu, vizual elementlər, brend və digər materiallar — VOLAURA, Inc.-ə və ya onun lisenziya verənlərinə məxsusdur. Bu Şərtlər sizə platformadan istifadə üçün məhdud, geri alına bilən, qeyri-eksklüziv hüquq verir. Mülkiyyət vermir.
        </p>
      </Section>

      <Section title="13. Zəmanətlərin məhdudluğu">
        <p>
          VOLAURA &laquo;olduğu kimi&raquo; və &laquo;mövcud olduğu həcmdə&raquo; təqdim edilir. Biz hər zaman xətasız, fasiləsiz, tam dəqiq və ya müəyyən məqsəd üçün tam uyğun olacağını zəmanət vermirik.
        </p>
      </Section>

      <Section title="14. Məsuliyyətin məhdudlaşdırılması">
        <p>
          Qanunla icazə verilən maksimum həddə dolayı zərərlərə, gəlir və imkan itkisinə, reputasiya zərərinə, məlumat itkisinə görə məsuliyyət daşımırıq. Əgər qanun başqa cür tələb etmirsə, VOLAURA, Inc.-in bu Şərtlərlə bağlı ümumi məsuliyyəti son 12 ayda sizdən alınmış məbləğlə və ya ödəniş olmayıbsa <strong className="text-foreground">100 ABŞ dolları</strong> ilə məhdudlaşır.
        </p>
      </Section>

      <Section title="15. Tətbiq olunan hüquq">
        <p>
          Bu Şərtlər Delaware ştatının qanunları ilə tənzimlənir, amma yaşadığınız ölkənin məcburi istehlakçı hüquqları sizə tətbiq olunmağa davam edir.
        </p>
      </Section>

      <Section title="16. Dəyişikliklər">
        <p>
          Bu Şərtləri yeniləyə bilərik. Əhəmiyyətli dəyişiklik olarsa, platformada və ya email ilə xəbər verə bilərik. Yenilənmiş Şərtlər qüvvəyə mindikdən sonra xidmətdən istifadə etməyə davam etsəniz, yeni versiya tətbiq olunur.
        </p>
      </Section>

      <Section title="17. Əlaqə">
        <p>
          Suallar üçün: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>
    </>
  );
}

/* ──────────────────────────  EN  ────────────────────────── */
function TermsEn() {
  return (
    <>
      <Section title="1. Introduction">
        <p>
          These Terms of Service govern your use of VOLAURA, operated by <strong className="text-foreground">VOLAURA, Inc.</strong>, a Delaware C-Corporation. By using VOLAURA, you agree to these Terms. Contact: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>

      <Section title="2. What the service is">
        <p>
          VOLAURA is a platform for professional skill assessment, profile verification, and verified talent presentation. We do <strong className="text-foreground">not</strong> guarantee jobs, hiring outcomes, income, admission, certification, or any specific result.
        </p>
      </Section>

      <Section title="3. Age requirement">
        <p>
          You must be <strong className="text-foreground">18 or older</strong> to use VOLAURA.
        </p>
      </Section>

      <Section title="4. Your account">
        <p>
          When you create an account, you must provide accurate information, keep your login credentials reasonably secure, and take responsibility for activity under your account. If you sign in with Google, you are also responsible for the security of that Google account.
        </p>
      </Section>

      <Section title="5. Using assessments and the platform">
        <p>
          You agree that you will answer assessments honestly, not impersonate another person, not try to manipulate scores or outcomes, and use the platform only for lawful purposes. We may use fraud, integrity, and security checks to protect the platform.
        </p>
      </Section>

      <Section title="6. Your content">
        <p>
          You may submit information such as profile details, assessment responses, and an optional photo. You keep ownership of your content. But you give us a limited right to host, store, process, display, and use it as needed to operate, secure, and support the service. If you upload an optional photo, you must have the right to use it.
        </p>
      </Section>

      <Section title="7. AI and automated scoring">
        <p>
          VOLAURA may use AI systems and rule-based systems to process assessment responses and platform signals. These systems may generate scores, insights, recommendations, and matching or quality signals. AI outputs can be useful, but they are not guaranteed to be perfect. You and any third party using the platform should not treat AI output as the only basis for an important decision. VOLAURA is not designed to make legally significant decisions about you solely through automation. If automated processing significantly affects you, you may ask for further explanation and human review.
        </p>
      </Section>

      <Section title="8. Payments">
        <p>
          If we offer paid features or subscriptions: payments are processed by Stripe, you must provide accurate billing information, pricing, renewal, and refund terms will be shown with the relevant offering, Stripe may apply its own terms and privacy rules. We do not store your payment card details ourselves.
        </p>
      </Section>

      <Section title="9. Prohibited use">
        <p>
          You may not access another person&apos;s account without permission, reverse-engineer, disrupt, or damage the platform, spam, scrape, or abuse the service with automation, upload malicious code, create fake profiles, fake assessment activity, or fake evidence, break the law or violate someone else&apos;s rights.
        </p>
      </Section>

      <Section title="10. Suspension and termination">
        <p>
          We may limit, suspend, or terminate access if you break these Terms or create risk for the platform or other users. You may also ask to close your account at any time.
        </p>
      </Section>

      <Section title="11. Privacy">
        <p>
          Our handling of personal data is explained in our Privacy Policy. By using VOLAURA, you understand that the Privacy Policy also applies to your use of the service.
        </p>
      </Section>

      <Section title="12. Intellectual property">
        <p>
          The platform itself — including its software, design, branding, text, and visual materials — belongs to VOLAURA, Inc. or its licensors. These Terms give you a limited, revocable, non-exclusive right to use the service. They do not transfer ownership.
        </p>
      </Section>

      <Section title="13. Warranty disclaimer">
        <p>
          VOLAURA is provided on an &quot;as is&quot; and &quot;as available&quot; basis. We do not promise that the service will always be uninterrupted, error-free, fully accurate, or fit for every specific purpose.
        </p>
      </Section>

      <Section title="14. Limitation of liability">
        <p>
          To the maximum extent allowed by law, VOLAURA, Inc. will not be liable for indirect, incidental, special, consequential, or similar damages, including lost profits, lost opportunities, reputation harm, or loss of data. Unless the law says otherwise, our total liability under these Terms is limited to the amount you paid us in the previous 12 months, or <strong className="text-foreground">USD 100</strong> if you paid nothing.
        </p>
      </Section>

      <Section title="15. Governing law">
        <p>
          These Terms are governed by the laws of the State of Delaware, except that mandatory consumer protections in your place of residence still apply where required.
        </p>
      </Section>

      <Section title="16. Changes">
        <p>
          We may update these Terms from time to time. If a change is material, we may notify you in the product or by email. If you keep using the service after the updated Terms take effect, the new version applies.
        </p>
      </Section>

      <Section title="17. Contact">
        <p>
          Questions: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>
    </>
  );
}

/* ──────────────────────────  helpers  ────────────────────────── */
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-xl font-semibold font-headline text-foreground">{title}</h2>
      {children}
    </section>
  );
}

function Mail({ children }: { children: string }) {
  return (
    <a href={`mailto:${children}`} className="text-primary underline">
      {children}
    </a>
  );
}
