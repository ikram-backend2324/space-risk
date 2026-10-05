"""
Localized domain content: hazards, regions, recommendations, forecast narrative.

Order of every entry: uz (Uzbek Latin), en, ru, kaa (Karakalpak Latin, 2016 alphabet:
á ǵ ı ń ó ú w y; capital of ı is Í).
"""


def L(uz, en, ru, kaa):
    return {"uz": uz, "en": en, "ru": ru, "kaa": kaa}


HAZARD_TEXT = {
    "seismic": (
        L("Zilzila", "Earthquake", "Землетрясение", "Jer silkiniw"),
        L("Seysmik faollik va yer qobigʻi deformatsiyasi",
          "Seismic activity and crustal deformation",
          "Сейсмическая активность и деформация земной коры",
          "Seysmikalıq aktivlik hám jer qabıǵınıń deformaciyası"),
    ),
    "flood": (
        L("Sel va toshqin", "Mudflows and floods", "Сели и паводки", "Sel hám tasqın"),
        L("Togʻ sellari, daryo toshqinlari, suv omborlari xavfi",
          "Mountain mudflows, river floods and reservoir failures",
          "Горные сели, речные паводки, угроза прорыва водохранилищ",
          "Taw selleri, dárya tasqınları, suw saqlaǵıshlardıń qáwipi"),
    ),
    "drought": (
        L("Qurgʻoqchilik", "Drought", "Засуха", "Qurǵaqshılıq"),
        L("Yogʻin tanqisligi va oʻsimliklar stressi",
          "Rainfall deficit and vegetation stress",
          "Дефицит осадков и стресс растительности",
          "Jawın-shashınnıń jetispewi hám ósimlikler stressi"),
    ),
    "heatwave": (
        L("Issiqlik toʻlqini", "Heatwave", "Волны жары", "Íssılıq tolqını"),
        L("Ekstremal harorat va shahar issiqlik orollari",
          "Extreme temperatures and urban heat islands",
          "Экстремальные температуры и городские острова тепла",
          "Ekstremal temperatura hám qalalıq ıssılıq atawları"),
    ),
    "landslide": (
        L("Koʻchki va surilish", "Landslides", "Оползни и обвалы", "Kóshki hám jer jılısıwı"),
        L("Yonbagʻir surilishi, qor koʻchkilari",
          "Slope failures and snow avalanches",
          "Сход склонов и снежные лавины",
          "Qıyalıqlardıń jılısıwı, qar kóshkileri"),
    ),
    "dust": (
        L("Chang-tuz boʻronlari", "Dust and salt storms", "Пыльно-солевые бури", "Shań-duz boranları"),
        L("Orol tubidan koʻtarilgan tuzli changlar",
          "Salty dust lifted from the dried Aral seabed",
          "Солёная пыль со дна высохшего Арала",
          "Qurıǵan Aral teńiziniń túbinen kóterilgen duzlı shań"),
    ),
    "water": (
        L("Suv tanqisligi", "Water scarcity", "Дефицит воды", "Suw tanqıslıǵı"),
        L("Yer osti va yer usti suv zaxiralari kamayishi",
          "Shrinking groundwater and surface-water reserves",
          "Сокращение запасов подземных и поверхностных вод",
          "Jer astı hám jer ústi suw qorlarınıń azayıwı"),
    ),
    "air": (
        L("Havo ifloslanishi", "Air pollution", "Загрязнение воздуха", "Hawanıń pataslanıwı"),
        L("PM2.5, NO₂, SO₂ konsentratsiyalari",
          "PM2.5, NO₂ and SO₂ concentrations",
          "Концентрации PM2.5, NO₂, SO₂",
          "PM2.5, NO₂, SO₂ koncentraciyaları"),
    ),
    "desertification": (
        L("Choʻllanish", "Desertification", "Опустынивание", "Shólge aylanıw"),
        L("Yer degradatsiyasi va shoʻrlanish",
          "Land degradation and soil salinisation",
          "Деградация земель и засоление почв",
          "Jer degradaciyası hám duzlanıw"),
    ),
}

# Satellite/data source names that contain words (others are proper names, unchanged).
SOURCE_TEXT = {
    "GNSS tarmogʻi": L("GNSS tarmogʻi", "GNSS network", "Сеть GNSS", "GNSS tarmaǵı"),
    "GPM yogʻingarchilik": L("GPM yogʻingarchilik", "GPM precipitation", "Осадки GPM", "GPM jawın-shashın"),
    "SMAP tuproq namligi": L("SMAP tuproq namligi", "SMAP soil moisture", "Влажность почвы SMAP", "SMAP topıraq ızǵarlıǵı"),
    "Sentinel-2 suv yuzasi": L("Sentinel-2 suv yuzasi", "Sentinel-2 surface water", "Поверхностные воды Sentinel-2", "Sentinel-2 suw beti"),
    "Yer usti stansiyalari": L("Yer usti stansiyalari", "Ground stations", "Наземные станции", "Jer ústi stanciyaları"),
    "Landsat arxivi": L("Landsat arxivi", "Landsat archive", "Архив Landsat", "Landsat arxivi"),
}

REGION_TEXT = {
    "toshkent-shahri": (
        L("Toshkent shahri", "Tashkent City", "город Ташкент", "Tashkent qalası"),
        L("Poytaxt: yuqori aholi zichligi, seysmik faol zona (1966-yil zilzilasi), shahar issiqlik oroli.",
          "The capital: high population density, a seismically active zone (1966 earthquake), urban heat island.",
          "Столица: высокая плотность населения, сейсмически активная зона (землетрясение 1966 года), городской остров тепла.",
          "Paytaxt: xalıqtıń joqarı tıǵızlıǵı, seysmikalıq aktiv zona (1966-jılǵı jer silkiniw), qalalıq ıssılıq atawı."),
    ),
    "toshkent-viloyati": (
        L("Toshkent viloyati", "Tashkent Region", "Ташкентская область", "Tashkent wálayatı"),
        L("Chatqol va Qurama togʻlari, Angren–Olmaliq sanoat zonasi, sel va koʻchki xavfi yuqori.",
          "Chatkal and Kurama mountains, the Angren–Almalyk industrial zone, high mudflow and landslide risk.",
          "Чаткальский и Кураминский хребты, Ангрен-Алмалыкская промышленная зона, высокий риск селей и оползней.",
          "Shatqal hám Qurama tawları, Angren–Almalıq sanaat zonası, sel hám kóshki qáwipi joqarı."),
    ),
    "andijon": (
        L("Andijon viloyati", "Andijan Region", "Андижанская область", "Ándijan wálayatı"),
        L("Fargʻona vodiysining eng zich hududi, kuchli seysmik faollik.",
          "The most densely populated part of the Fergana Valley, with strong seismic activity.",
          "Самая густонаселённая часть Ферганской долины, высокая сейсмическая активность.",
          "Ferǵana oypatınıń eń tıǵız aymaǵı, kúshli seysmikalıq aktivlik."),
    ),
    "namangan": (
        L("Namangan viloyati", "Namangan Region", "Наманганская область", "Namangan wálayatı"),
        L("Togʻ oldi hududlari, sel oqimlari va koʻchkilar.",
          "Foothill areas exposed to mudflows and landslides.",
          "Предгорные территории, селевые потоки и оползни.",
          "Taw aldı aymaqları, sel aǵımları hám kóshkiler."),
    ),
    "fargona": (
        L("Fargʻona viloyati", "Fergana Region", "Ферганская область", "Ferǵana wálayatı"),
        L("Sanoat va qishloq xoʻjaligi markazi, seysmik va ekologik bosim.",
          "An industrial and agricultural hub under seismic and environmental pressure.",
          "Промышленный и аграрный центр, сейсмическая и экологическая нагрузка.",
          "Sanaat hám awıl xojalıǵı orayı, seysmikalıq hám ekologiyalıq basım."),
    ),
    "sirdaryo": (
        L("Sirdaryo viloyati", "Syrdarya Region", "Сырдарьинская область", "Sırdárya wálayatı"),
        L("Mirzachoʻl tekisligi, shoʻrlanish, Sardoba suv ombori (2020) tajribasi.",
          "The Mirzachul (Hungry Steppe) plain, soil salinisation, lessons from the 2020 Sardoba reservoir failure.",
          "Мирзачульская равнина (Голодная степь), засоление почв, уроки прорыва Сардобинского водохранилища (2020).",
          "Mirzashól tegisligi, duzlanıw, Sardoba suw saqlaǵıshı (2020) tájiriybesi."),
    ),
    "jizzax": (
        L("Jizzax viloyati", "Jizzakh Region", "Джизакская область", "Jizzaq wálayatı"),
        L("Choʻl va togʻ oraligʻidagi hudud, suv tanqisligi oʻsmoqda.",
          "A region between desert and mountains where water scarcity is growing.",
          "Регион между пустыней и горами, дефицит воды растёт.",
          "Shól menen taw arasındaǵı aymaq, suw tanqıslıǵı artpaqta."),
    ),
    "samarqand": (
        L("Samarqand viloyati", "Samarkand Region", "Самаркандская область", "Samarqand wálayatı"),
        L("Zarafshon vodiysi, tarixiy meros obyektlari, seysmik xavf.",
          "The Zarafshan Valley, historic heritage sites, seismic hazard.",
          "Долина Зарафшана, объекты исторического наследия, сейсмическая опасность.",
          "Zarafshan oypatı, tariyxıy miyras obyektleri, seysmikalıq qáwip."),
    ),
    "qashqadaryo": (
        L("Qashqadaryo viloyati", "Kashkadarya Region", "Кашкадарьинская область", "Qashqadárya wálayatı"),
        L("Gaz sanoati (Muborak), issiq iqlim, sel xavfi togʻ hududlarida.",
          "Gas industry (Muborak), a hot climate and mudflow risk in mountain areas.",
          "Газовая промышленность (Мубарек), жаркий климат, селевая опасность в горных районах.",
          "Gaz sanaatı (Mubarek), ıssı klimat, taw aymaqlarında sel qáwipi."),
    ),
    "surxondaryo": (
        L("Surxondaryo viloyati", "Surkhandarya Region", "Сурхандарьинская область", "Surxandárya wálayatı"),
        L("Oʻzbekistonning eng issiq hududi, seysmik faol togʻlar.",
          "Uzbekistan's hottest region, with seismically active mountains.",
          "Самый жаркий регион Узбекистана, сейсмически активные горы.",
          "Ózbekstannıń eń ıssı aymaǵı, seysmikalıq aktiv tawlar."),
    ),
    "buxoro": (
        L("Buxoro viloyati", "Bukhara Region", "Бухарская область", "Buxara wálayatı"),
        L("Qizilqum choʻli chegarasi, Gazli zilzilalari (1976, 1984), suv tanqisligi.",
          "The edge of the Kyzylkum desert, the Gazli earthquakes (1976, 1984), water scarcity.",
          "Граница пустыни Кызылкум, Газлийские землетрясения (1976, 1984), дефицит воды.",
          "Qızılqum shóliniń shegarası, Gazli jer silkiniwleri (1976, 1984), suw tanqıslıǵı."),
    ),
    "navoiy": (
        L("Navoiy viloyati", "Navoi Region", "Навоийская область", "Nawayı wálayatı"),
        L("Kon-metallurgiya markazi, keng choʻl hududlari.",
          "A mining and metallurgy hub with vast desert areas.",
          "Горно-металлургический центр, обширные пустынные территории.",
          "Kán-metallurgiya orayı, keń shól aymaqları."),
    ),
    "xorazm": (
        L("Xorazm viloyati", "Khorezm Region", "Хорезмская область", "Xorezm wálayatı"),
        L("Amudaryo quyi oqimi, Orol inqirozi taʼsiri, shoʻrlanish.",
          "The lower Amu Darya, the impact of the Aral Sea crisis, soil salinisation.",
          "Низовья Амударьи, последствия Аральского кризиса, засоление почв.",
          "Ámiwdáryanıń tómengi aǵımı, Aral krizisiniń tásiri, duzlanıw."),
    ),
    "qoraqalpogiston": (
        L("Qoraqalpogʻiston Respublikasi", "Republic of Karakalpakstan", "Республика Каракалпакстан", "Qaraqalpaqstan Respublikası"),
        L("Orol dengizi ekologik falokati markazi: tuzli chang boʻronlari, choʻllanish.",
          "The epicentre of the Aral Sea environmental disaster: salty dust storms, desertification.",
          "Эпицентр экологической катастрофы Аральского моря: солевые пыльные бури, опустынивание.",
          "Aral teńizi ekologiyalıq apatınıń orayı: duzlı shań boranları, shólge aylanıw."),
    ),
}

# hazard -> [(title, text, priority), ...]
RECOMMENDATIONS = {
    "seismic": [
        (L("Binolarni seysmik audit qilish", "Seismic audit of buildings", "Сейсмический аудит зданий", "Imaratlardı seysmikalıq audit qılıw"),
         L("Maktab, shifoxona va koʻp qavatli uylarni 8–9 ballik zilzilaga chidamlilik boʻyicha tekshirish va kuchaytirish dasturini boshlash.",
           "Check schools, hospitals and high-rise housing for resistance to intensity 8–9 earthquakes and launch a retrofit programme.",
           "Проверить школы, больницы и многоэтажные дома на устойчивость к землетрясениям силой 8–9 баллов и запустить программу усиления.",
           "Mektepler, emlewxanalar hám kóp qabatlı úylerdi 8–9 ballıq jer silkiniwine shıdamlılıǵı boyınsha tekserip, bekkemlew baǵdarlamasın baslaw."),
         "high"),
        (L("InSAR monitoring", "InSAR monitoring", "InSAR-мониторинг", "InSAR monitoringi"),
         L("Sentinel-1 radar maʼlumotlari asosida yer qobigʻi deformatsiyasini har 6 kunda kuzatish.",
           "Track crustal deformation every 6 days using Sentinel-1 radar data.",
           "Отслеживать деформацию земной коры каждые 6 дней по радарным данным Sentinel-1.",
           "Sentinel-1 radar maǵlıwmatları tiykarında jer qabıǵınıń deformaciyasın hár 6 kúnde baqlaw."),
         "medium"),
    ],
    "flood": [
        (L("Sel erta ogohlantirish tizimi", "Mudflow early-warning system", "Система раннего оповещения о селях", "Sel haqqında erte eskertiw sisteması"),
         L("Togʻ soylarida avtomatik datchiklar va GPM yogʻin prognozlarini birlashtirib, aholiga SMS-ogohlantirish yuborish.",
           "Combine automatic sensors on mountain streams with GPM rainfall forecasts to send SMS alerts to residents.",
           "Объединить автоматические датчики на горных реках с прогнозами осадков GPM и рассылать жителям SMS-оповещения.",
           "Taw saylarındaǵı avtomat datchiklerdi GPM jawın boljawları menen birlestirip, xalıqqa SMS-eskertiw jiberiw."),
         "high"),
        (L("Suv omborlari xavfsizligi", "Reservoir safety", "Безопасность водохранилищ", "Suw saqlaǵıshlardıń qáwipsizligi"),
         L("Toʻgʻonlar holatini sunʼiy yoʻldosh va dron orqali muntazam tekshirish.",
           "Regularly inspect dams using satellite imagery and drones.",
           "Регулярно проверять состояние плотин с помощью спутников и дронов.",
           "Bógetlerdiń jaǵdayın jasalma joldas hám dronlar arqalı turaqlı túrde tekseriw."),
         "medium"),
    ],
    "drought": [
        (L("Tomchilatib sugʻorish", "Drip irrigation", "Капельное орошение", "Tamshılatıp suwǵarıw"),
         L("Qishloq xoʻjaligida suvni tejovchi texnologiyalarni subsidiyalash va 30% gacha suv tejash.",
           "Subsidise water-saving technologies in agriculture to cut water use by up to 30%.",
           "Субсидировать водосберегающие технологии в сельском хозяйстве и экономить до 30% воды.",
           "Awıl xojalıǵında suwdı únemleytuǵın texnologiyalardı subsidiyalap, 30% ke shekem suw únemlew."),
         "high"),
        (L("NDVI asosida hosil monitoringi", "NDVI-based crop monitoring", "Мониторинг урожая по NDVI", "NDVI tiykarında ónim monitoringi"),
         L("MODIS/Sentinel-2 vegetatsiya indekslari bilan qurgʻoqchilikni 4–6 hafta oldin aniqlash.",
           "Detect drought 4–6 weeks early with MODIS/Sentinel-2 vegetation indices.",
           "Выявлять засуху за 4–6 недель с помощью вегетационных индексов MODIS/Sentinel-2.",
           "MODIS/Sentinel-2 ósimlik indeksleri járdeminde qurǵaqshılıqtı 4–6 hápte aldın anıqlaw."),
         "medium"),
    ],
    "heatwave": [
        (L("Shahar issiqlik orollarini kamaytirish", "Reduce urban heat islands", "Сокращение городских островов тепла", "Qalalıq ıssılıq atawların azaytıw"),
         L("Yashil zonalar, salqin tomlar va soya beruvchi infratuzilmani kengaytirish.",
           "Expand green zones, cool roofs and shade-giving infrastructure.",
           "Расширять зелёные зоны, «холодные» крыши и затеняющую инфраструктуру.",
           "Jasıl zonalardı, salqın tóbelerdi hám saya beretuǵın infrastrukturanı keńeytiw."),
         "high"),
        (L("Issiqlik harakat rejasi", "Heat action plan", "План действий при жаре", "Íssılıq waqtındaǵı háreket rejesi"),
         L("+40°C dan yuqori kunlarda aholini ogohlantirish va salqinlash markazlarini ochish.",
           "Warn residents on days above +40°C and open cooling centres.",
           "Оповещать население в дни с температурой выше +40°C и открывать пункты охлаждения.",
           "+40°C-tan joqarı kúnlerde xalıqtı eskertip, salqınlatıw orayların ashıw."),
         "medium"),
    ],
    "landslide": [
        (L("Koʻchki xaritalash", "Landslide mapping", "Картирование оползней", "Kóshkilerdi kartaǵa túsiriw"),
         L("DEM va InSAR maʼlumotlari asosida xavfli yonbagʻirlarni aniqlab, qurilishni cheklash.",
           "Identify dangerous slopes from DEM and InSAR data and restrict construction there.",
           "Выявлять опасные склоны по данным DEM и InSAR и ограничивать там строительство.",
           "DEM hám InSAR maǵlıwmatları tiykarında qáwipli qıyalıqlardı anıqlap, qurılıstı sheklew."),
         "high"),
        (L("Yonbagʻirlarni mustahkamlash", "Slope stabilisation", "Укрепление склонов", "Qıyalıqlardı bekkemlew"),
         L("Daraxt ekish va drenaj tizimlari orqali surilish xavfini kamaytirish.",
           "Reduce slide risk by planting trees and installing drainage.",
           "Снижать риск оползней посадкой деревьев и дренажными системами.",
           "Terek egiw hám drenaj sistemaları arqalı jılısıw qáwipin azaytıw."),
         "medium"),
    ],
    "dust": [
        (L("Orol tubini oʻrmonlashtirish", "Afforest the Aral seabed", "Озеленение дна Арала", "Aral túbin toǵaylastırıw"),
         L("Saksovul va boshqa choʻl oʻsimliklarini ekish orqali tuzli chang manbalarini barqarorlashtirish.",
           "Stabilise salty dust sources by planting saxaul and other desert plants.",
           "Закреплять источники солевой пыли посадками саксаула и других пустынных растений.",
           "Seksewil hám basqa da shól ósimliklerin egiw arqalı duzlı shań dereklerin turaqlastırıw."),
         "high"),
        (L("Chang boʻroni prognozi", "Dust-storm forecasting", "Прогноз пыльных бурь", "Shań boranı boljawı"),
         L("Sentinel-5P va MODIS AOD maʼlumotlari bilan 48 soatlik chang prognozi xizmatini yoʻlga qoʻyish.",
           "Launch a 48-hour dust forecast service using Sentinel-5P and MODIS AOD data.",
           "Запустить 48-часовой прогноз пыльных бурь на основе данных Sentinel-5P и MODIS AOD.",
           "Sentinel-5P hám MODIS AOD maǵlıwmatları menen 48 saatlıq shań boljawı xızmetin jolǵa qoyıw."),
         "medium"),
    ],
    "water": [
        (L("Suv resurslarini raqamli boshqarish", "Digital water management", "Цифровое управление водными ресурсами", "Suw resursların cifrlı basqarıw"),
         L("GRACE-FO yer osti suv maʼlumotlari asosida kanallar va quduqlarda smart-hisoblagichlar joriy etish.",
           "Install smart meters on canals and wells, guided by GRACE-FO groundwater data.",
           "Устанавливать умные счётчики на каналах и скважинах с учётом данных GRACE-FO о подземных водах.",
           "GRACE-FO jer astı suw maǵlıwmatları tiykarında kanallar hám qudıqlarǵa aqıllı esaplaǵıshlar ornatıw."),
         "high"),
        (L("Kanallarni betonlash", "Line irrigation canals", "Бетонирование каналов", "Kanallardı betonlaw"),
         L("Sugʻorish tarmogʻidagi filtratsiya yoʻqotishlarini kamaytirish.",
           "Cut seepage losses in the irrigation network.",
           "Сократить потери на фильтрацию в оросительной сети.",
           "Suwǵarıw tarmaǵındaǵı filtraciya joǵaltıwların azaytıw."),
         "medium"),
    ],
    "air": [
        (L("Emissiyalarni nazorat qilish", "Emission control", "Контроль выбросов", "Emissiyalardı qadaǵalaw"),
         L("Sanoat korxonalarida uzluksiz emissiya monitoringi va Sentinel-5P NO₂ xaritalari bilan solishtirish.",
           "Introduce continuous emission monitoring at industrial plants and compare it with Sentinel-5P NO₂ maps.",
           "Внедрить непрерывный мониторинг выбросов на предприятиях и сверять его с картами NO₂ Sentinel-5P.",
           "Sanaat kárxanalarında úzliksiz emissiya monitoringin engizip, Sentinel-5P NO₂ kartaları menen salıstırıw."),
         "high"),
        (L("Toza transport", "Clean transport", "Чистый транспорт", "Taza transport"),
         L("Elektr jamoat transporti va velo-infratuzilmani kengaytirish.",
           "Expand electric public transport and cycling infrastructure.",
           "Развивать электрический общественный транспорт и велоинфраструктуру.",
           "Elektr jámáát transportın hám velo-infrastrukturanı keńeytiw."),
         "low"),
    ],
    "desertification": [
        (L("Yer degradatsiyasini toʻxtatish", "Halt land degradation", "Остановить деградацию земель", "Jer degradaciyasın toqtatıw"),
         L("Shoʻrlangan yerlarni yuvish, almashlab ekish va choʻlga chidamli ekinlarni joriy etish.",
           "Leach salinised land, rotate crops and introduce drought-tolerant crops.",
           "Промывать засолённые земли, вводить севооборот и засухоустойчивые культуры.",
           "Duzlanǵan jerlerdi juwıw, almaslap egiw hám qurǵaqshılıqqa shıdamlı eginlerdi engiziw."),
         "high"),
        (L("Landsat 40 yillik tahlil", "40-year Landsat analysis", "40-летний анализ Landsat", "Landsat 40 jıllıq talqılaw"),
         L("Yer qoplami oʻzgarishini arxiv tasvirlari orqali baholab, ustuvor hududlarni belgilash.",
           "Assess land-cover change from archive imagery and set priority areas.",
           "Оценить изменения земного покрова по архивным снимкам и определить приоритетные территории.",
           "Arxiv súwretleri arqalı jer qaplamınıń ózgeriwin bahalap, áhmiyetli aymaqlardı belgilew."),
         "low"),
    ],
}

NARRATIVE = {
    "summary": L(
        "{region} uchun {year}-yilgacha boʻlgan umumiy xavf indeksi {score}/100 — “{level}” darajada. Eng kuchli tahdidlar: {top}.",
        "{region}: the overall risk index up to {year} is {score}/100 — “{level}” level. The strongest threats are {top}.",
        "Общий индекс риска для региона «{region}» до {year} года составляет {score}/100 — уровень «{level}». Наиболее серьёзные угрозы: {top}.",
        "{region} ushın {year}-jılǵa shekemgi ulıwma qáwip indeksi {score}/100 — «{level}» dárejede. Eń kúshli qáwipler: {top}.",
    ),
    "rising": L(
        "Iqlim oʻzgarishi sababli {list} xavfi har yili ortib bormoqda, shu sababli moslashuv choralarini hozirdan rejalashtirish tavsiya etiladi.",
        "Because of climate change, the risk of {list} is rising every year, so adaptation measures should be planned now.",
        "Из-за изменения климата такие угрозы, как {list}, усиливаются с каждым годом, поэтому меры адаптации стоит планировать уже сейчас.",
        "Klimattıń ózgeriwi sebepli {list} qáwipi jıl sayın artıp barmaqta, sonlıqtan beyimlesiw ilajların házirden rejelestiriw usınıladı.",
    ),
    "geological": L(
        "Xavflar asosan geologik xarakterga ega — tayyorgarlik va infratuzilma barqarorligi asosiy omil.",
        "The hazards are mainly geological — preparedness and resilient infrastructure are the key factors.",
        "Угрозы носят преимущественно геологический характер — ключевую роль играют готовность и устойчивость инфраструктуры.",
        "Qáwipler tiykarınan geologiyalıq xarakterge iye — tayarlıq hám infrastrukturanıń turaqlılıǵı tiykarǵı faktor.",
    ),
    "population": L(
        "Aholi soni yuqori (~{n} mln) — taʼsir ostidagi odamlar koʻp.",
        "Large population (~{n} million) — many people are exposed.",
        "Высокая численность населения (~{n} млн) — под угрозой много людей.",
        "Xalıq sanı joqarı (~{n} mln) — tásir astındaǵı adamlar kóp.",
    ),
}

LEVEL_TEXT = {
    "low": L("Past", "Low", "Низкий", "Tómen"),
    "moderate": L("Oʻrtacha", "Moderate", "Умеренный", "Ortasha"),
    "high": L("Yuqori", "High", "Высокий", "Joqarı"),
    "critical": L("Kritik", "Critical", "Критический", "Kritikalıq"),
}

PRIORITY_TEXT = {
    "high": L("Yuqori", "High", "Высокий", "Joqarı"),
    "medium": L("Oʻrta", "Medium", "Средний", "Orta"),
    "low": L("Past", "Low", "Низкий", "Tómen"),
}

MONTHS_SHORT = L("oy", "mo", "мес.", "ay")
