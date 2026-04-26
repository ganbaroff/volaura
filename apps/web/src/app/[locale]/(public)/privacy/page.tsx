import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

/**
 * Privacy Policy v2 — 2026-05-01 effective
 *
 * Source: GPT-5 generated 2026-04-26, courier-delivered by CEO.
 * Cross-referenced against GDPR (EUR-Lex CELEX 32016R0679),
 * California Civil Code §§ 1798.100/.105/.106/.110/.115/.130,
 * Azerbaijan Law on Personal Data.
 *
 * Bilingual inline JSX (AZ + EN). Locale-conditional rendering.
 * Replaces stub i18n keys (privacy.s1..s7) — keys retained in
 * common.json for backward compat but no longer read here.
 *
 * Canonical AZ + EN markdown source: for-ceo/legal/privacy-2026-05-01.md
 */
export const metadata: Metadata = {
  title: "Privacy Policy — Volaura",
};

export default async function PrivacyPage({
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
            {isAz ? "Məxfilik Siyasəti" : "Privacy Policy"}
          </h1>
          <p className="text-muted-foreground text-sm">
            {isAz ? "Qüvvəyə minmə tarixi: 1 may 2026" : "Effective date: 2026-05-01"}
          </p>
        </div>

        <div className="prose prose-invert prose-sm max-w-none space-y-8 text-sm leading-relaxed text-muted-foreground">
          {isAz ? <PrivacyAz /> : <PrivacyEn />}
        </div>

        <div className="mt-16 pt-8 border-t border-white/10 text-center text-xs text-muted-foreground">
          <p>
            © 2026 VOLAURA, Inc. ·{" "}
            <Link href={`/${locale}/terms`} className="hover:text-foreground transition-colors">
              {isAz ? "İstifadə Şərtləri" : "Terms of Service"}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

/* ──────────────────────────  AZ  ────────────────────────── */
function PrivacyAz() {
  return (
    <>
      <Section title="VOLAURA məxfiliyə necə yanaşır">
        <p>
          Bu Məxfilik Siyasəti VOLAURA, Inc. üçün keçərlidir. VOLAURA, Inc. Delaware ştatında qeydiyyatdan keçmiş C-Corporation-dır. Biz VOLAURA platformasını idarə edirik — peşəkar bacarıqların qiymətləndirilməsi və təsdiqlənməsi üçün verified professional talent platform.
        </p>
        <p>
          Bu sənəd sadə dildə izah edir: hansı məlumatları topladığımızı, niyə topladığımızı, kimlə paylaşdığımızı, nə qədər saxladığımızı və sizin hansı hüquqlarınızın olduğunu.
        </p>
        <p>
          Əlaqə: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>

      <Section title="Hansı məlumatları toplayırıq">
        <p>
          Biz aşağıdakı məlumatları toplaya bilərik: email ünvanı, ad və ya display name, hesab məlumatları, assesment cavabları, assesment nəticələri və skorlar, profil məlumatları, opsional profil fotosu, Google OAuth istifadə etdikdə Google hesabından gələn əsas məlumatlar, ödənişlə bağlı metadata (Stripe vasitəsilə), texniki məlumatlar (IP, device/browser məlumatı, təhlükəsizlik və audit logları).
        </p>
        <p>
          Biz kart məlumatlarını özümüz saxlamırıq. Ödənişlər Stripe tərəfindən işlənir.
        </p>
      </Section>

      <Section title="Məlumatı haradan alırıq">
        <p>
          Məlumatı birbaşa sizdən, Google OAuth-dan əgər siz Google ilə giriş edirsinizsə, Stripe-dan ödəniş və abunə statusu ilə bağlı, sizi platformaya dəvət edən təşkilat və ya istifadəçidən, və xidmətin təhlükəsiz işləməsi üçün yaranan texniki loglardan alırıq.
        </p>
        <p>Bu, GDPR Article 13 və Article 14 şəffaflıq tələblərinə uyğun məlumatlandırmadır.</p>
      </Section>

      <Section title="Məlumatı niyə işləyirik">
        <p>
          Hesab yaratmaq və idarə etmək, assesmentləri təqdim etmək və qiymətləndirmək, profilinizi və verified nəticələri göstərmək, təhlükəsizlik və audit, dəstək sorğularına cavab vermək, ödənişləri idarə etmək, platformanı yaxşılaşdırmaq, qanuni öhdəliklərimizi yerinə yetirmək.
        </p>
      </Section>

      <Section title="Hüquqi əsaslar">
        <p>
          GDPR üçün biz əsasən bu hüquqi əsaslara söykənirik: müqavilənin icrası, razılıq, qanuni maraq, hüquqi öhdəlik. Azərbaycan qanunvericiliyinə görə məlumatlar əsasən sizin razılığınızla, xidmətin göstərilməsi üçün zəruri olduqda, və ya qanuni əsas olduqda işlənir.
        </p>
      </Section>

      <Section title="AI və avtomatlaşdırılmış emal">
        <p>
          VOLAURA assesment cavablarını və digər platforma siqnallarını AI və qayda əsaslı sistemlərlə emal edə bilər: skor çıxarmaq, nəticələri izah etmək, insight və tövsiyələr yaratmaq, uyğunlaşma və keyfiyyət siqnalları formalaşdırmaq.
        </p>
        <p>Bu emal profilinq və avtomatlaşdırılmış qiymətləndirmə elementlərini əhatə edə bilər.</p>
        <p>
          <strong className="text-foreground">Vacib:</strong> VOLAURA sizin üçün təkbaşına hüquqi və ya oxşar dərəcədə əhəmiyyətli qərar verməməyə çalışır. Platforma nəticələri qərar dəstəyi kimi təqdim edilir. Əgər belə emal sizə əhəmiyyətli təsir göstərərsə, siz insan baxışı istəyə bilərsiniz, öz mövqeyinizi təqdim edə bilərsiniz, nəticəyə etiraz edə bilərsiniz, əlavə izah tələb edə bilərsiniz.
        </p>
        <p>Bu bölmə GDPR Article 22 və Azərbaycan qanunvericiliyində avtomatlaşdırılmış emala etiraz hüququnu nəzərə alır.</p>
      </Section>

      <Section title="Məlumatı kimlə paylaşırıq">
        <p>
          Məlumatı yalnız lazım olduqda paylaşırıq: Supabase (verilənlər bazası və auth infrastrukturu, ABŞ/Aİ regionları), Vercel (frontend hosting və edge çatdırılma, Aİ edge), Railway (backend hosting, ABŞ), Google OAuth (giriş üçün), Stripe (ödənişlərin işlənməsi üçün), hüquqi öhdəlik olduqda məhkəmə, tənzimləyici və ya dövlət orqanları ilə, sizin açıq yönləndirməniz olduqda digər tərəflərlə.
        </p>
        <p>Biz şəxsi məlumatlarınızı satmırıq.</p>
      </Section>

      <Section title="Transsərhəd ötürmə">
        <p>
          Məlumatlar yaşadığınız ölkədən kənarda, o cümlədən ABŞ və Aİ-də işlənə və saxlanıla bilər. Tələb olunduqda biz müqaviləvi, təşkilati və texniki qoruma tədbirlərindən istifadə edirik.
        </p>
      </Section>

      <Section title="Məlumatı nə qədər saxlayırıq">
        <p>
          Hesab məlumatı — hesab aktiv olduğu müddətdə. Assesment cavabları və nəticələri — xidmət, tarixçə və doğrulama məqsədləri üçün lazım olduğu müddətdə. Opsional foto — siz silənə və ya hesab bağlanana qədər. Ödəniş və mühasibat məlumatları — qanunla tələb olunan müddət ərzində. Təhlükəsizlik logları — təhlükəsizlik və audit üçün məqbul müddət ərzində.
        </p>
        <p>
          Məlumat artıq lazım olmadıqda onu silirik, anonimləşdiririk və ya arxivləşdiririk. Azərbaycan qanunvericiliyinə uyğun olaraq məqsəd aradan qalxdıqda məlumat gecikdirilmədən məhv edilməlidir, istisna hallardan başqa.
        </p>
      </Section>

      <Section title="Hüquqlarınız">
        <p>
          Sizin aşağıdakı hüquqlarınız ola bilər: məlumatınıza çıxış almaq, məlumatın düzəldilməsini istəmək, məlumatın silinməsini istəmək, emalın məhdudlaşdırılmasını istəmək, etiraz etmək, razılığı geri çəkmək, məlumatın ixracını istəmək, məlumatın mənbəyi barədə soruşmaq, avtomatlaşdırılmış emala etiraz etmək, şikayət vermək.
        </p>
        <p>
          GDPR üçün adətən sorğulara 1 ay ərzində cavab veririk. California üçün tətbiq olunarsa adətən 45 gün ərzində cavab veririk. Azərbaycan qanunvericiliyinə görə tətbiq olunan hallarda qanunda nəzərdə tutulan müddətlərə əməl edirik.
        </p>
        <p>
          Sorğu göndərmək üçün: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>

      <Section title="California residents üçün əlavə qeyd">
        <p>
          Əgər siz California sakinisinizsə və CCPA/CPRA sizə tətbiq olunursa, siz hansı məlumatı topladığımızı bilmək, məlumatınızın surətini almaq, düzəliş istəmək, silinmə istəmək, ayrı-seçkiliyə məruz qalmamaq hüququna maliksiniz.
        </p>
        <p>Hazırda biz şəxsi məlumatlarınızı satmırıq və cross-context behavioral advertising üçün paylaşmırıq.</p>
      </Section>

      <Section title="Yaş məhdudiyyəti">
        <p>
          VOLAURA yalnız <strong className="text-foreground">18 yaş və yuxarı</strong> istifadəçilər üçündür. 18 yaşdan aşağı şəxslər üçün nəzərdə tutulmayıb.
        </p>
      </Section>

      <Section title="Dəyişikliklər">
        <p>Bu siyasəti zaman-zaman yeniləyə bilərik. Əgər vacib dəyişiklik olsa, platformada və ya email ilə xəbər verə bilərik.</p>
      </Section>

      <Section title="Əlaqə">
        <p>
          Məxfilik və məlumat hüquqları ilə bağlı əlaqə: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>
    </>
  );
}

/* ──────────────────────────  EN  ────────────────────────── */
function PrivacyEn() {
  return (
    <>
      <Section title="Who we are">
        <p>
          This Privacy Policy applies to <strong className="text-foreground">VOLAURA, Inc.</strong>, a Delaware C-Corporation. We operate VOLAURA, a verified professional talent platform for skill assessment and verification.
        </p>
        <p>This policy explains: what data we collect, why we collect it, who we share it with, how long we keep it, and what rights you have.</p>
        <p>
          Contact: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>

      <Section title="What we collect">
        <p>
          We may collect: email address, name or display name, account details, assessment answers, assessment results and scores, profile information, optional profile photo, basic data from Google OAuth if you sign in with Google, payment metadata from Stripe, technical data such as IP address, browser/device data, and security logs.
        </p>
        <p>
          We do <strong className="text-foreground">not</strong> store your payment card details ourselves.
        </p>
      </Section>

      <Section title="Where the data comes from">
        <p>
          We collect personal data: directly from you, from Google OAuth if you choose that sign-in method, from Stripe for payment and subscription status, from an organization or user that invites you, from technical logs created while operating the service.
        </p>
        <p>
          This section is intended to support <strong className="text-foreground">GDPR Article 13 and 14</strong> transparency requirements.
        </p>
      </Section>

      <Section title="Why we use your data">
        <p>
          We use personal data to: create and manage your account, deliver assessments and generate results, show your profile and verified outcomes, protect the service, prevent abuse, and keep audit logs, respond to support requests, manage payments and subscriptions, improve the platform, comply with legal obligations.
        </p>
      </Section>

      <Section title="Legal bases">
        <p>
          For users in the EEA, our main legal bases are: performance of a contract, consent, legitimate interests, legal obligations. For users in Azerbaijan, processing is mainly based on your consent, what is necessary to provide the service, or another legal basis allowed by law. Optional photos and optional profile fields are generally based on your choice.
        </p>
      </Section>

      <Section title="AI processing and automated decision-making">
        <p>
          VOLAURA may use AI systems and rule-based systems to: score assessment responses, explain results, generate insights and recommendations, create matching or quality signals.
        </p>
        <p>This may involve profiling and automated processing.</p>
        <p>
          <strong className="text-foreground">Important:</strong> we aim not to make decisions about you that are based solely on automated processing where those decisions produce legal effects or similarly significant effects. VOLAURA results are meant to support decisions, not replace human judgment. If this kind of processing applies, you may ask for human review, an explanation, a chance to express your point of view, and a way to contest the outcome.
        </p>
        <p>
          This section is intended to reflect <strong className="text-foreground">GDPR Article 22</strong>.
        </p>
      </Section>

      <Section title="Who we share data with">
        <p>
          We share personal data only where needed: Supabase (database and authentication infrastructure, US/EU), Vercel (frontend hosting and EU edge delivery), Railway (backend hosting, US), Google OAuth (sign-in), Stripe (payments), courts, regulators, or authorities where legally required, other parties if you clearly ask us to or consent to it.
        </p>
        <p>
          We do <strong className="text-foreground">not</strong> sell your personal information.
        </p>
      </Section>

      <Section title="International transfers">
        <p>
          Your data may be processed outside your country, including in the United States and the European Union. Where required, we use contractual, organizational, and technical safeguards for international transfers.
        </p>
      </Section>

      <Section title="How long we keep data">
        <p>
          We keep data only as long as needed: account data while your account is active, assessment answers and results as long as needed to provide the service, history, and verification, optional photo until you remove it or close your account, payment and accounting data for the period required by law, security logs for a reasonable security and audit period.
        </p>
        <p>When we no longer need data, we delete it, anonymize it, or archive it where legally required.</p>
      </Section>

      <Section title="Your rights">
        <p>
          Depending on where you live, you may have the right to: access your data, correct your data, delete your data, restrict processing, object to processing, withdraw consent, export your data, ask about the source of the data, object to automated decision-making, and file a complaint.
        </p>
        <p>
          For <strong className="text-foreground">GDPR</strong> requests, we usually respond within <strong className="text-foreground">1 month</strong>. For <strong className="text-foreground">California</strong> requests, where applicable, we usually respond within <strong className="text-foreground">45 days</strong>. For <strong className="text-foreground">Azerbaijan</strong>, we follow the timelines required by applicable law.
        </p>
        <p>
          To make a request, email: <Mail>hello@volaura.app</Mail>
        </p>
      </Section>

      <Section title="California privacy notice">
        <p>
          If you are a California resident and the CCPA/CPRA applies to you, you may have the right to: know what personal information we collect, access a copy of it, request correction, request deletion, and not be discriminated against for using your rights.
        </p>
        <p>
          We currently do <strong className="text-foreground">not</strong> sell personal information or share it for cross-context behavioral advertising.
        </p>
      </Section>

      <Section title="Age limit">
        <p>
          VOLAURA is for people <strong className="text-foreground">18 and older</strong>. It is not intended for minors.
        </p>
      </Section>

      <Section title="Changes">
        <p>We may update this Privacy Policy from time to time. If a change is important, we may notify you in the product or by email.</p>
      </Section>

      <Section title="Contact">
        <p>
          For privacy questions or rights requests: <Mail>hello@volaura.app</Mail>
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
