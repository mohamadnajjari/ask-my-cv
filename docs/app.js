// Ask my CV – portfolio page: languages, theme, scroll effects and the chat.
// No libraries. The English text lives in the HTML (it works without JavaScript and search
// engines see it); German and Persian replace it from the dictionary below.
"use strict";

// Backend URL. For local testing only, ?api=http://localhost:8000 overrides it; any other
// address is ignored, so nobody can send a link that routes visitors' questions elsewhere.
const API_OVERRIDE = new URLSearchParams(location.search).get("api") || "";
const API_URL = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(API_OVERRIDE)
  ? API_OVERRIDE
  : "https://cv-api.onsorex.com";

const root = document.documentElement;
root.classList.remove("no-js");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- texts
const T = {
  en: {
    docTitle: "Mohammad Najjari – AI Engineer",
    typed: ["AI integration", "computer vision", "LLM applications", "deployment & MLOps"],
    ph: "Ask about my experience…",
    hello: "Hi! I'm Mohammad's AI assistant. Ask me about his experience, projects or availability, or tap a question below.",
    chips: [["about", "Introduce him in one minute"], ["roles", "Which roles is he looking for?"], ["work-permit", "Is he allowed to work in Germany?"], ["thesis", "What did he achieve at BHS?"], ["onsorex", "What is Onsorex?"], ["why-hire", "Why should we hire him?"], ["contact", "How can I contact him?"]],
    instant: "⚡ Instant answer", ai: "AI answer", sources: "Based on",
    limited: "The AI part is resting for now (daily limit), so this is a prepared answer. For anything else, email Mohammad directly.",
    neterr: "Couldn't reach the assistant. Check your connection and try again, or email Mohammad directly.",
    aria: { lang: "Language", theme: "Light or dark theme", close: "Close", send: "Send" },
  },
  de: {
    docTitle: "Mohammad Najjari – KI-Ingenieur",
    typed: ["KI-Integration", "Computer Vision", "LLM-Anwendungen", "Deployment & MLOps"],
    ph: "Fragen Sie nach meiner Erfahrung…",
    hello: "Hallo! Ich bin Mohammads KI-Assistent. Fragen Sie nach seiner Erfahrung, seinen Projekten oder seiner Verfügbarkeit – oder tippen Sie unten auf eine Frage.",
    chips: [["about", "Stellen Sie ihn kurz vor"], ["roles", "Welche Stellen sucht er?"], ["work-permit", "Darf er in Deutschland arbeiten?"], ["thesis", "Was hat er bei BHS erreicht?"], ["onsorex", "Was ist Onsorex?"], ["why-hire", "Warum sollten wir ihn einstellen?"], ["contact", "Wie erreiche ich ihn?"]],
    instant: "⚡ Sofortantwort", ai: "KI-Antwort", sources: "Quellen",
    limited: "Der KI-Teil pausiert gerade (Tageslimit), daher eine vorbereitete Antwort. Für alles Weitere schreiben Sie Mohammad gern direkt.",
    neterr: "Der Assistent ist nicht erreichbar. Bitte Verbindung prüfen und erneut versuchen oder Mohammad direkt per E-Mail kontaktieren.",
    aria: { lang: "Sprache", theme: "Helles oder dunkles Design", close: "Schließen", send: "Senden" },
    "nav.about": "Über mich", "nav.experience": "Erfahrung", "nav.projects": "Projekte", "nav.skills": "Kenntnisse", "nav.contact": "Kontakt",
    "hero.badge": "Offen für Vollzeitstellen · Frankfurt am Main",
    "hero.role": "KI-Ingenieur ·",
    "hero.pitch": "Ich bringe KI in die Praxis: Ich habe ein industrielles Computer-Vision-Modell vom Forschungsprototyp in Richtung Produktion gebracht und entwickle Onsorex, eine live laufende, mehrsprachige Web-App mit abgesicherter LLM-Schicht. Fragen Sie meinen KI-Assistenten alles, was Sie in einem ersten Gespräch fragen würden.",
    "hero.live": "live",
    "cta.chat": "KI-Assistenten fragen", "cta.email": "E-Mail schreiben",
    "stat.f1": "F1-Score, vorher 0,41", "stat.images": "annotierte Industriebilder", "stat.tests": "automatisierte Tests in Onsorex", "stat.langs": "Sprachen: Persisch, Englisch, Deutsch",
    "about.kicker": "Über mich", "about.title": "Ein Lösungsfinder, der liefert",
    "about.p1": "Ich habe einen <strong>M.Eng. in Künstlicher Intelligenz</strong> der Technischen Hochschule Deggendorf. Bei der <strong>BHS Intralogistics</strong> war ich Werkstudent, habe meine Masterarbeit geschrieben und dann als AI &amp; Computer Vision Engineer gearbeitet – mit dem Ziel, ein Modell zur Schadenstiefe fabriktauglich zu machen.",
    "about.p2": "Davor habe ich einen Online-Marktplatz gegründet und allein entwickelt. Heute baue ich <strong>Onsorex</strong>: Dort formuliert ein LLM nur Fakten um, die mein eigener Code berechnet hat, und jede Antwort wird geprüft, bevor jemand sie sieht.",
    "about.p3": "Ich suche Stellen als <strong>AI Engineer, AI Integration Engineer oder Computer Vision Engineer</strong> und bin auch offen für Datenrollen.",
    "fact.loc": "Frankfurt am Main", "fact.locd": "vor Ort, hybrid im Umkreis von ~100 km oder remote in Deutschland",
    "fact.start": "Sofort verfügbar", "fact.startd": "Vollzeit, Start so bald wie möglich",
    "fact.permit": "Darf in Vollzeit arbeiten", "fact.permitd": "Unterlagen im Bewerbungsprozess",
    "fact.langs": "Persisch · Englisch C1 · Deutsch B1", "fact.langsd": "Deutsch wird laufend besser; Führerschein Klasse B",
    "exp.kicker": "Erfahrung", "exp.title": "Von Industriekameras zu produktiver KI",
    "job1.title": "Gründer &amp; Entwickler, Onsorex", "job1.when": "04/2026 – heute", "job1.org": "Eigenes Produkt · onsorex.com",
    "job1.a": "Allein entworfen und gebaut: eine live laufende, mehrsprachige Web-App (EN/DE/FA, rechts-nach-links), die Marktpreise in der eigenen Währung zeigt und verständlich erklärt.",
    "job1.b": "Abgesicherte LLM-Schicht: Das Modell formuliert nur berechnete Fakten um; Guardrails blockieren Anlageempfehlungen, Prognosen und erfundene Zahlen. Gebaut und getestet, in Produktion noch nicht aktiv.",
    "job1.c": "Next.js, FastAPI, PostgreSQL/TimescaleDB, Valkey, Docker bei Hetzner, Caddy, Cloudflare, GitHub Actions, Sentry.",
    "job1.m": "Backend-Tests · 12 End-to-End-Tests",
    "job2.title": "AI &amp; Computer Vision Engineer",
    "job2.org": "BHS Intralogistics GmbH · Neutraubling · Werkstudent → Masterarbeit → Ingenieur",
    "job2.a": "Ein KI-System zur <strong>Schadenstiefenbestimmung</strong> vom Forschungsprototyp in Richtung industrieller Einsatz gebracht und in die Prüfabläufe der Produktion integriert.",
    "job2.b": "Das Modell robust gemacht: Fehlklassifikationen analysiert, schadensfokussierte Bildausschnitte, Vorverarbeitung für wechselndes Licht und Bildqualität.",
    "job2.c": "Deployment und Validierung unter Hardware- und Latenzgrenzen der Produktion (TensorFlow, OpenCV); Industriekameras und Sensoren installiert und kalibriert.",
    "job2.m": "Fehler",
    "job3.title": "Gründer &amp; Full-Stack-Entwickler, Irantimche.com", "job3.org": "Online-Marktplatz · Teheran",
    "job3.a": "Die gesamte Plattform allein programmiert, Frontend und Backend, bevor es KI-Programmierassistenten gab (MVC, PHP, MySQL).",
    "job3.b": "Die Linux-Produktionsumgebung betrieben: Deployments, Fehlersuche, Dokumentation. Beendet für das KI-Studium in Deutschland.",
    "job4.title": "Freiberuflicher Webentwickler",
    "job4.a": "Responsive Websites für Kunden mit WordPress und eigenen Frontends; Schritt für Schritt hin zu serverseitiger, datenbankgestützter Entwicklung.",
    "proj.kicker": "Projekte", "proj.title": "Was ich gebaut habe",
    "p1.status": "Live",
    "p1.text": "Marktpreise in Ihrer Währung und Sprache, in einfachen Worten erklärt. Ein modularer Monolith mit deterministischer Fakten-Engine und einer LLM-Schicht, die weder Anlageempfehlungen geben noch Zahlen erfinden kann.",
    "p2.status": "Masterarbeit · BHS", "p2.title": "Schadenstiefenbestimmung",
    "p2.text": "Ein ResNet-50-Klassifikator, der die Schadenstiefe aus industriellen 2D-Bildern schätzt, trainiert mit 5.886 annotierten Bildern. F1-Score 0,41 → 0,85, Top-1-Fehler 50 % → 23 %.",
    "p3.status": "Live · auf dieser Seite",
    "p3.text": "Der Assistent auf dieser Seite. Häufige Fragen bekommen vorbereitete Antworten, Wiederholungen kommen aus einem Cache – beides kostenlos; der Rest bekommt einen schlanken Claude-Aufruf mit passenden Textstellen. Budgets und Kontingente pro Besucher sorgen dafür, dass Missbrauch nichts kostet.",
    "p3.link": "Quellcode →",
    "skills.kicker": "Kenntnisse", "skills.title": "Womit ich arbeite",
    "s1": "KI-Engineering &amp; LLM-Integration", "s2": "Machine Learning &amp; Computer Vision", "s3": "Deployment, MLOps &amp; Daten", "s4": "Programmiersprachen &amp; Integration",
    "s4.cam": "Kamera- &amp; Sensorkalibrierung", "s4.hw": "Hardware-Software-Integration",
    "edu.kicker": "Ausbildung", "edu.title": "Lernen, das sich aufbaut",
    "d1": "M.Eng. Artificial Intelligence for Smart Sensors and Actuators", "d1d": "Technische Hochschule Deggendorf · Note 2,1",
    "d2": "B.Eng. Fertigungs- und Produktionstechnik", "d2d": "Azad-Universität, Iran · deutsche Note 1,3",
    "d3": "Abschluss Flugzeuginstandhaltung (Associate Degree)", "d3d": "Civil Aviation Technology College, Teheran",
    "langs.title": "Sprachen", "l.fa": "Persisch", "l.native": "Muttersprache", "l.en": "Englisch", "l.de": "Deutsch",
    "contact.kicker": "Kontakt", "contact.title": "Lassen Sie uns sprechen",
    "contact.text": "Ich freue mich über Einladungen zum Gespräch per E-Mail oder LinkedIn. Oder fragen Sie zuerst meinen Assistenten – er antwortet jederzeit auf Deutsch, Englisch oder Persisch.",
    "footer": "Keine Cookies, keine Tracker. Chatfragen gehen an den Server des Assistenten und an die Claude-API von Anthropic und werden nicht mit Ihrer Adresse gespeichert.",
    "fab": "Fragen Sie mich",
    "chat.title": "Mohammads KI-Assistent", "chat.sub": "Antwortet aus meinem Lebenslauf · kann sich irren", "chat.label": "Ihre Frage",
    "chat.note": 'Fragen gehen an die Claude-API von Anthropic, wenn keine vorbereitete Antwort passt. <a href="https://github.com/mohamadnajjari/ask-my-cv" target="_blank" rel="noopener">So funktioniert es</a>',
  },
  fa: {
    docTitle: "محمد نجاری – مهندس هوش مصنوعی",
    typed: ["یکپارچه‌سازی هوش مصنوعی", "بینایی ماشین", "کاربردهای مدل‌های زبانی", "استقرار و MLOps"],
    ph: "درباره تجربه من بپرسید…",
    hello: "سلام! من دستیار هوش مصنوعی محمد هستم. درباره تجربه، پروژه‌ها یا زمان شروع کار او بپرسید، یا یکی از پرسش‌های زیر را انتخاب کنید.",
    chips: [["about", "او را در یک دقیقه معرفی کن"], ["roles", "دنبال چه نقش‌هایی است؟"], ["work-permit", "آیا اجازه کار در آلمان دارد؟"], ["thesis", "در BHS چه کرد؟"], ["onsorex", "Onsorex چیست؟"], ["why-hire", "چرا او را استخدام کنیم؟"], ["contact", "چطور با او تماس بگیرم؟"]],
    instant: "⚡ پاسخ فوری", ai: "پاسخ هوش مصنوعی", sources: "بر اساس",
    limited: "بخش هوش مصنوعی فعلاً استراحت می‌کند (سقف روزانه)، پس این یک پاسخ آماده است. برای پرسش‌های دیگر مستقیم به محمد ایمیل بزنید.",
    neterr: "اتصال به دستیار ممکن نشد. اتصال اینترنت را بررسی کنید و دوباره امتحان کنید، یا مستقیم به محمد ایمیل بزنید.",
    aria: { lang: "زبان", theme: "حالت روشن یا تیره", close: "بستن", send: "ارسال" },
    "nav.about": "درباره من", "nav.experience": "تجربه", "nav.projects": "پروژه‌ها", "nav.skills": "مهارت‌ها", "nav.contact": "تماس",
    "hero.badge": "آماده همکاری تمام‌وقت · فرانکفورت",
    "hero.name": 'محمد <span class="gradient-text">نجاری</span>',
    "hero.role": "مهندس هوش مصنوعی ·",
    "hero.pitch": "من هوش مصنوعی را به دنیای واقعی می‌آورم: یک مدل بینایی ماشین صنعتی را از نمونه پژوهشی به سمت تولید بردم و Onsorex را می‌سازم؛ یک وب‌اپلیکیشن چندزبانه فعال با لایه هوش مصنوعی کنترل‌شده. هر چیزی که در اولین تماس می‌پرسید، از دستیار هوش مصنوعی من بپرسید.",
    "hero.live": "فعال",
    "cta.chat": "از دستیار من بپرسید", "cta.email": "ایمیل بزنید",
    "stat.f1": "امتیاز F1، قبلاً ۰٫۴۱", "stat.images": "تصویر صنعتی برچسب‌خورده", "stat.tests": "آزمون خودکار در Onsorex", "stat.langs": "زبان: فارسی، انگلیسی، آلمانی",
    "about.kicker": "درباره من", "about.title": "حل‌کننده مسئله‌ای که کار را به نتیجه می‌رساند",
    "about.p1": "من <strong>کارشناسی ارشد هوش مصنوعی</strong> را از دانشگاه فنی دگندورف گرفته‌ام. در <strong>BHS Intralogistics</strong> دانشجوی کارآموز بودم، پایان‌نامه‌ام را نوشتم و سپس مهندس هوش مصنوعی و بینایی ماشین شدم تا یک مدل تشخیص عمق آسیب را برای کارخانه قابل استفاده کنم.",
    "about.p2": "پیش از آن یک بازار آنلاین را راه‌اندازی کردم و به تنهایی ساختم. اکنون <strong>Onsorex</strong> را می‌سازم؛ جایی که مدل زبانی فقط واقعیت‌هایی را بازنویسی می‌کند که کد خودم محاسبه کرده، و هر پاسخ پیش از نمایش بررسی می‌شود.",
    "about.p3": "به دنبال نقش‌های <strong>مهندس هوش مصنوعی، مهندس یکپارچه‌سازی هوش مصنوعی یا مهندس بینایی ماشین</strong> هستم و برای نقش‌های داده هم آماده‌ام.",
    "fact.loc": "فرانکفورت", "fact.locd": "حضوری، ترکیبی تا حدود ۱۰۰ کیلومتر، یا دورکاری در آلمان",
    "fact.start": "آماده شروع", "fact.startd": "تمام‌وقت، در اولین فرصت",
    "fact.permit": "اجازه کار تمام‌وقت", "fact.permitd": "مدارک در روند استخدام ارائه می‌شود",
    "fact.langs": "فارسی · انگلیسی C1 · آلمانی B1", "fact.langsd": "آلمانی در حال پیشرفت؛ گواهینامه رانندگی کلاس B",
    "exp.kicker": "تجربه", "exp.title": "از دوربین‌های کارخانه تا هوش مصنوعی در تولید",
    "job1.title": "بنیان‌گذار و توسعه‌دهنده، Onsorex", "job1.when": "۰۴/۲۰۲۶ – اکنون", "job1.org": "محصول مستقل · onsorex.com",
    "job1.a": "طراحی و ساخت یک‌نفره یک وب‌اپلیکیشن چندزبانه فعال (انگلیسی، آلمانی، فارسی راست‌به‌چپ) که قیمت بازارها را به ارز خود کاربر نشان می‌دهد و به زبان ساده توضیح می‌دهد.",
    "job1.b": "لایه مدل زبانی کنترل‌شده: مدل فقط واقعیت‌های محاسبه‌شده را بازنویسی می‌کند؛ کنترل‌ها توصیه سرمایه‌گذاری، پیش‌بینی و عدد ساختگی را رد می‌کنند. ساخته و آزمایش شده، هنوز در نسخه اصلی فعال نیست.",
    "job1.c": "Next.js، FastAPI، PostgreSQL/TimescaleDB، Valkey، Docker روی Hetzner، Caddy، Cloudflare، GitHub Actions، Sentry.",
    "job1.m": "آزمون بک‌اند · ۱۲ آزمون سرتاسری",
    "job2.title": "مهندس هوش مصنوعی و بینایی ماشین",
    "job2.org": "BHS Intralogistics GmbH · نویترابلینگ · کارآموز ← پایان‌نامه ← مهندس",
    "job2.a": "پیشبرد سامانه هوش مصنوعی <strong>تعیین عمق آسیب</strong> از نمونه پژوهشی به سمت کاربرد صنعتی و ادغام آن در فرایند بازرسی تولید.",
    "job2.b": "مقاوم‌سازی مدل: تحلیل طبقه‌بندی‌های اشتباه، برش تصویر متمرکز بر آسیب، پیش‌پردازش برای نور و کیفیت متغیر تصویر.",
    "job2.c": "استقرار و اعتبارسنجی با محدودیت‌های سخت‌افزار و زمان پاسخ در تولید (TensorFlow، OpenCV)؛ نصب و کالیبره کردن دوربین‌ها و حسگرهای صنعتی.",
    "job2.m": "خطا",
    "job3.title": "بنیان‌گذار و توسعه‌دهنده فول‌استک، Irantimche.com", "job3.org": "بازار آنلاین · تهران",
    "job3.a": "نوشتن کل پلتفرم به تنهایی، فرانت‌اند و بک‌اند، پیش از وجود دستیارهای برنامه‌نویسی هوش مصنوعی (MVC، PHP، MySQL).",
    "job3.b": "اداره محیط تولید لینوکس: استقرار، رفع اشکال، مستندسازی. برای تحصیل هوش مصنوعی در آلمان به پایان رسید.",
    "job4.title": "توسعه‌دهنده وب آزاد",
    "job4.a": "وب‌سایت‌های واکنش‌گرا برای مشتریان با WordPress و فرانت‌اند اختصاصی؛ و حرکت تدریجی به سمت توسعه سمت سرور و پایگاه داده.",
    "proj.kicker": "پروژه‌ها", "proj.title": "چیزهایی که ساخته‌ام",
    "p1.status": "فعال",
    "p1.text": "قیمت بازارها به ارز و زبان شما، با توضیح ساده. یک مونولیت ماژولار با موتور واقعیت‌های قطعی و لایه مدل زبانی که نه توصیه سرمایه‌گذاری می‌دهد و نه عدد می‌سازد.",
    "p2.status": "پایان‌نامه ارشد · BHS", "p2.title": "تعیین عمق آسیب",
    "p2.text": "یک طبقه‌بند ResNet-50 که عمق آسیب را از تصاویر دوبعدی صنعتی تخمین می‌زند و با ۵۸۸۶ تصویر برچسب‌خورده آموزش دیده است. امتیاز F1 از ۰٫۴۱ به ۰٫۸۵ و خطا از ۵۰٪ به ۲۳٪.",
    "p3.status": "فعال · در همین صفحه",
    "p3.text": "دستیار همین صفحه. پرسش‌های رایج پاسخ آماده می‌گیرند و پرسش‌های تکراری از حافظه پاسخ داده می‌شوند، هر دو رایگان؛ بقیه با یک فراخوانی سبک Claude همراه با متن‌های مرتبط پاسخ می‌گیرند. بودجه و سهمیه هر بازدیدکننده باعث می‌شود سوءاستفاده هزینه‌ای نداشته باشد.",
    "p3.link": "کد منبع ←",
    "skills.kicker": "مهارت‌ها", "skills.title": "ابزارهای کار من",
    "s1": "مهندسی هوش مصنوعی و یکپارچه‌سازی مدل‌های زبانی", "s2": "یادگیری ماشین و بینایی ماشین", "s3": "استقرار، MLOps و داده", "s4": "زبان‌های برنامه‌نویسی و یکپارچه‌سازی",
    "s4.cam": "کالیبره کردن دوربین و حسگر", "s4.hw": "یکپارچه‌سازی سخت‌افزار و نرم‌افزار",
    "edu.kicker": "تحصیلات", "edu.title": "یادگیری که روی هم انباشته می‌شود",
    "d1": "کارشناسی ارشد هوش مصنوعی برای حسگرها و عملگرهای هوشمند", "d1d": "دانشگاه فنی دگندورف · نمره ۲٫۱",
    "d2": "کارشناسی مهندسی تکنولوژی ساخت و تولید", "d2d": "دانشگاه آزاد · معادل آلمانی ۱٫۳",
    "d3": "کاردانی تعمیر و نگهداری هواپیما", "d3d": "دانشکده فنی هواپیمایی کشوری، تهران",
    "langs.title": "زبان‌ها", "l.fa": "فارسی", "l.native": "زبان مادری", "l.en": "انگلیسی", "l.de": "آلمانی",
    "contact.kicker": "تماس", "contact.title": "بیایید صحبت کنیم",
    "contact.text": "از دعوت به مصاحبه از طریق ایمیل یا لینکدین استقبال می‌کنم. یا اول از دستیارم بپرسید؛ هر زمان به فارسی، انگلیسی یا آلمانی پاسخ می‌دهد.",
    "footer": "بدون کوکی و بدون ردیاب. پرسش‌های گفت‌وگو به سرور دستیار و API Claude شرکت Anthropic فرستاده می‌شوند و همراه نشانی شما ذخیره نمی‌شوند.",
    "fab": "از من بپرسید",
    "chat.title": "دستیار هوش مصنوعی محمد", "chat.sub": "پاسخ از روی رزومه من · ممکن است اشتباه کند", "chat.label": "پرسش شما",
    "chat.note": 'وقتی پاسخ آماده‌ای نباشد، پرسش به API Claude شرکت Anthropic فرستاده می‌شود. <a href="https://github.com/mohamadnajjari/ask-my-cv" target="_blank" rel="noopener">چطور کار می‌کند</a>',
  },
};

// ---------------------------------------------------------------- preferences
// Remembered in this browser only (a convenience; the page works without it).
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private mode: fine */ } },
};
const browserLang = (navigator.language || "en").toLowerCase();
let lang = store.get("lang") || (browserLang.startsWith("fa") ? "fa" : browserLang.startsWith("de") ? "de" : "en");
if (!T[lang]) lang = "en";

function setTheme(theme) {
  root.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]').content = theme === "light" ? "#f5f7fb" : "#070b14";
}
setTheme(store.get("theme") || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"));
$("theme").onclick = () => {
  const next = root.dataset.theme === "light" ? "dark" : "light";
  setTheme(next);
  store.set("theme", next);
};

// Our own fixed texts only (never visitor or model text): safe to set as HTML.
function setLang(l) {
  lang = l;
  const t = T[l];
  root.lang = l;
  root.dir = l === "fa" ? "rtl" : "ltr";
  document.title = t.docTitle;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    if (el.dataset.en === undefined) el.dataset.en = el.innerHTML;
    el.innerHTML = l === "en" ? el.dataset.en : (t[el.dataset.i18n] ?? el.dataset.en);
  });
  $("q").placeholder = t.ph;
  document.querySelector(".seg").setAttribute("aria-label", t.aria.lang);
  $("theme").setAttribute("aria-label", t.aria.theme);
  $("close").setAttribute("aria-label", t.aria.close);
  $("send").setAttribute("aria-label", t.aria.send);
  document.querySelectorAll(".seg button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === l)));
  renderChips();
  typer.restart();
}
document.querySelectorAll(".seg button").forEach((b) => {
  b.onclick = () => { setLang(b.dataset.lang); store.set("lang", b.dataset.lang); };
});

// ---------------------------------------------------------------- hero typewriter
const typer = (() => {
  const el = $("typed");
  let timer = 0, word = 0;
  function run(text, i, deleting) {
    el.textContent = text.slice(0, i);
    let next;
    if (!deleting && i < text.length) next = () => run(text, i + 1, false);
    else if (!deleting) { timer = setTimeout(() => run(text, i, true), 1800); return; }
    else if (i > 0) next = () => run(text, i - 1, true);
    else { word = (word + 1) % T[lang].typed.length; next = () => run(T[lang].typed[word], 0, false); }
    timer = setTimeout(next, deleting ? 35 : 70);
  }
  return {
    restart() {
      clearTimeout(timer);
      word = 0;
      if (reduced) { el.textContent = T[lang].typed[0]; return; }
      run(T[lang].typed[0], 0, false);
    },
  };
})();

// ---------------------------------------------------------------- scroll effects
// Sections slide in once, from the side their data-from names (mirrored on Persian pages).
const counted = new WeakSet();
function countUp(el) {
  if (counted.has(el)) return;
  counted.add(el);
  const target = Number(el.dataset.count), decimals = Number(el.dataset.decimals || 0);
  const fmt = (v) => (el.dataset.group !== undefined
    ? Math.round(v).toLocaleString("en-US") : v.toFixed(decimals)) + (el.dataset.suffix || "");
  if (reduced) { el.textContent = fmt(target); return; }
  const start = performance.now(), ms = 1400;
  const step = (now) => {
    const p = Math.min((now - start) / ms, 1);
    el.textContent = fmt(target * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
document.querySelectorAll(".stats .reveal").forEach((el, i) => el.style.setProperty("--delay", `${i * 90}ms`));
const revealer = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    e.target.classList.add("in");
    e.target.querySelectorAll("[data-count]").forEach(countUp);
    revealer.unobserve(e.target);
  }
}, { threshold: 0.15, rootMargin: "0px 0px -6% 0px" });
document.querySelectorAll(".reveal").forEach((el) => revealer.observe(el));

// The menu marks the section being read.
const links = [...document.querySelectorAll(".nav-links a")];
const spy = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) links.forEach((a) => a.classList.toggle("active", a.hash === `#${e.target.id}`));
  }
}, { rootMargin: "-45% 0px -50% 0px" });
document.querySelectorAll("main section[id]").forEach((s) => spy.observe(s));

// One cheap scroll handler, at most once per frame: page progress (top line and drifting
// background lights) and how far the timeline's line has grown.
const timeline = $("timeline");
let ticking = false;
function onScroll() {
  ticking = false;
  const max = document.documentElement.scrollHeight - innerHeight;
  root.style.setProperty("--scroll", max > 0 ? (scrollY / max).toFixed(4) : "0");
  const r = timeline.getBoundingClientRect();
  const p = Math.min(Math.max((innerHeight * 0.65 - r.top) / r.height, 0), 1);
  timeline.style.setProperty("--tl", p.toFixed(4));
}
addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
onScroll();

// Project cards lean slightly towards the pointer (mouse only, and never with reduced motion).
if (!reduced && matchMedia("(pointer: fine)").matches) {
  document.querySelectorAll(".project").forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      card.style.setProperty("--ry", `${(x - 0.5) * 8}deg`);
      card.style.setProperty("--rx", `${(0.5 - y) * 8}deg`);
      card.style.setProperty("--mx", `${x * 100}%`);
      card.style.setProperty("--my", `${y * 100}%`);
    });
    card.addEventListener("pointerleave", () => {
      card.style.setProperty("--rx", "0deg");
      card.style.setProperty("--ry", "0deg");
    });
  });
}

// ---------------------------------------------------------------- chat
const log = $("log"), form = $("form"), q = $("q"), send = $("send"), fab = $("fab"), chat = $("chat");
const history = [];
let greeted = false;

function openChat() {
  document.body.classList.add("chat-open");
  fab.setAttribute("aria-expanded", "true");
  chat.setAttribute("aria-hidden", "false");
  if (!greeted) { greeted = true; addRow("bot", md(T[lang].hello)); }
  setTimeout(() => q.focus(), 250);
}
function closeChat() {
  document.body.classList.remove("chat-open");
  fab.setAttribute("aria-expanded", "false");
  chat.setAttribute("aria-hidden", "true");
  fab.focus();
}
document.querySelectorAll("[data-open-chat]").forEach((b) => (b.onclick = openChat));
$("close").onclick = closeChat;
addEventListener("keydown", (e) => { if (e.key === "Escape" && document.body.classList.contains("chat-open")) closeChat(); });

// Suggestion buttons ask for prepared answers by ID: instant, and they cost nothing.
const used = new Set();
function renderChips() {
  const box = $("chips");
  box.textContent = "";
  for (const [id, label] of T[lang].chips) {
    if (used.has(id)) continue;
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.onclick = () => { used.add(id); b.remove(); ask(label, id); };
    box.appendChild(b);
  }
}

// Minimal, safe Markdown: escape everything first, then allow bold, italics, links and bullets.
function md(src) {
  const esc = src.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const inline = (s) => s
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+|mailto:[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/(^|\s)(https?:\/\/[^\s<]+[^\s<.,;:!?)])/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
  const out = [];
  let list = null;
  for (const line of esc.split("\n")) {
    const m = line.match(/^\s*[-*•]\s+(.*)/);
    if (m) { (list ||= []).push(`<li>${inline(m[1])}</li>`); continue; }
    if (list) { out.push(`<ul>${list.join("")}</ul>`); list = null; }
    if (line.trim()) out.push(`<p>${inline(line)}</p>`);
  }
  if (list) out.push(`<ul>${list.join("")}</ul>`);
  return out.join("");
}
const text = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function addRow(kind, html, meta = "") {
  const row = document.createElement("div");
  row.className = `row ${kind}`;
  if (kind !== "user") {
    const img = document.createElement("img");
    img.src = "avatar.webp"; img.alt = ""; img.width = 28; img.height = 28;
    row.appendChild(img);
  }
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = html + meta;
  row.appendChild(bubble);
  log.appendChild(row);
  log.scrollTop = log.scrollHeight;
  return row;
}
function typing() {
  return addRow("bot typing", "<i></i><i></i><i></i>");
}
const pause = (ms) => new Promise((r) => setTimeout(r, ms));

function metaFor(data) {
  const t = T[lang];
  if (data.kind === "limited") return `<div class="meta"><span>${text(t.limited)}</span></div>`;
  if (data.kind === "prepared" || data.kind === "cached") return `<div class="meta"><span class="tag fast">${t.instant}</span></div>`;
  const src = (data.sources || []).map((s) => s.split(" › ").pop()).join("; ");
  return `<div class="meta"><span class="tag">${t.ai}</span>${src ? `<span>${t.sources}: ${text(src)}</span>` : ""}</div>`;
}

async function ask(question, preparedId) {
  question = question.trim();
  if (!question || send.disabled) return;
  addRow("user", text(question));
  history.push({ role: "user", content: question });
  q.value = ""; autosize();
  send.disabled = true;
  const dots = typing();
  const started = performance.now();
  try {
    const body = { messages: history.slice(-5), lang };
    if (preparedId) body.prepared_id = preparedId;
    const r = await fetch(API_URL.replace(/\/$/, "") + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : T[lang].neterr);
    // Instant answers still show the dots briefly, so the reply doesn't feel like a jump.
    const wait = 500 - (performance.now() - started);
    if (wait > 0 && !reduced) await pause(wait);
    dots.remove();
    history.push({ role: "assistant", content: data.answer });
    addRow("bot", md(data.answer), metaFor(data));
  } catch (e) {
    dots.remove();
    history.pop();
    addRow("err", md(e.message && !/fetch|network/i.test(e.message) ? e.message : T[lang].neterr));
  } finally {
    send.disabled = false;
    q.focus();
  }
}

function autosize() { q.style.height = "auto"; q.style.height = `${Math.min(q.scrollHeight, 120)}px`; }
q.addEventListener("input", autosize);
q.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(q.value); } });
form.addEventListener("submit", (e) => { e.preventDefault(); ask(q.value); });

setLang(lang);
