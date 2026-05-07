import json
import logging
import os
import re
import sys

INPUT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "directories.json")
)
OUTPUT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "categories.json")
)

# Categories are checked in order — first match wins.
# Multi-word keywords: substring match. Single-word: word-boundary match (\b).
# Governance is last and acts as catch-all.
CATEGORIES = [
    {
        "name": "commodity-prices",
        "description": "Harga Komoditas",
        "keywords": [
            "harga beras", "harga minyak", "harga daging ayam", "harga telur",
            "harga gula", "harga cabai", "harga cabe", "harga bawang",
            "harga jagung pipil", "harga kedelai", "harga daging sapi",
            "penyaluran kredit usaha rakyat", "kredit usaha rakyat menurut",
        ],
    },
    {
        "name": "livestock-fisheries",
        "description": "Peternakan & Perikanan",
        "keywords": [
            "populasi ternak", "ternak besar", "ternak kecil", "ternak unggas",
            "produksi daging", "produksi telur", "produksi susu",
            "inseminasi buatan", "ternak terpotong", "pengiriman ternak",
            "luas kolam", "pembudidaya kolam", "produksi ikan",
        ],
    },
    {
        "name": "agriculture-food",
        "description": "Pertanian & Ketahanan Pangan",
        "keywords": [
            "luas tanam", "luas panen", "luas areal",
            "hasil produksi palawija", "hasil produksi sayur", "hasil produksi buah",
            "hasil produksi perkebunan", "hasil produksi biofarmaka",
            "hasil produksi tanaman", "tanaman buah",
            "baku lahan", "penyuluh pertanian", "lembaga petani",
            "penyaluran pupuk", "ketahanan pangan", "pola pangan harapan",
            "tanaman pangan", "hortikultura", "biofarmaka",
            "peningkatan produksi tanaman", "peningkatan produksi hortikultura",
            "peningkatan produksi komoditas",
        ],
    },
    {
        "name": "health",
        "description": "Kesehatan",
        "keywords": [
            "kesehatan ibu", "kesehatan bayi", "kesehatan balita",
            "kesehatan usia", "kesehatan calon pengantin", "catin",
            "imunisasi", "puskesmas", "rumah sakit", "rsud",
            "status gizi", "vitamin a", "peserta kb aktif", "kb aktif",
            "kematian ibu", "kematian bayi", "angka kematian",
            "phbs", "jamban sehat", "air minum",
            "tenaga medis", "tenaga kesehatan", "teknik medik",
            "hiv", "tuberkulosis", "hipertensi", "diabetes",
            "stunting", "rawat inap", "rawat jalan",
            "limbah medis", "bayi lahir", "bblr", "stop babs",
            "fasilitas kesehatan", "bina keluarga", "pik-r",
            "kampung kb", "kunjungan rumah sakit", "kasus medis",
            "pd3i", "uci dan siaga", "odgj",
            "alos", "bor", "bto", "gdr", "ndr",
            "fertility rate", "resiko stunting", "gizi balita",
            "bangga kencana", "tempat pengelolaan pangan",
            "pengawasan ikl", "klinik", "infeksi nosokomial",
            "pemberian asi", "vit a", "keluarga sehat", "tuberkolosis",
        ],
    },
    {
        "name": "education",
        "description": "Pendidikan & Literasi",
        "keywords": [
            "guru tk", "guru sd", "guru smp", "guru pendidikan kesetaraan",
            "siswa tk", "siswa sd", "siswa smp", "siswa pkbm",
            "siswa pendidikan kesetaraan",
            "data satuan tk", "data satuan sd", "data satuan smp",
            "satuan pendidikan kesetaraan",
            "jumlah tk", "jumlah sd", "jumlah smp",
            "jumlah pendidikan kesetaraan",
            "status akreditasi", "sarana dan prasarana sd", "sarana dan prasarana smp",
            "angka melek huruf", "angka partisipasi", "rata rata lama sekolah",
            "rerata lama sekolah", "indeks pendidikan",
            "numerasi", "literasi sd", "literasi smp",
            "iklim keamanan sd", "iklim keamanan smp",
            "inklusivitas", "kebinekaan",
            "koleksi buku", "anggota perpustakaan", "pengunjung perpustakaan",
            "indeks minat baca", "indeks literasi",
            "gedung olahraga", "klub olahraga", "atlet berprestasi",
            "organisasi pemuda", "sekolah tk", "paud",
        ],
    },
    {
        "name": "demographics",
        "description": "Demografi & Kependudukan",
        "keywords": [
            "jumlah penduduk", "kepemilikan akta kelahiran",
            "kepemilikan akta perkawinan", "kepemilikan akta perceraian",
            "kepemilikan akta kematian", "kepemilikan cetak kk",
            "kelompok umur", "penduduk pindah", "kepadatan penduduk",
            "kepemilikan ktp", "kepemilikan kia",
            "indeks kepuasan layanan kependudukan",
            "luas kecamatan", "jarak dari ibukota", "ketinggian wilayah",
            "total fertility rate", "ktp elektronik",
        ],
    },
    {
        "name": "tourism-culture",
        "description": "Pariwisata & Budaya",
        "keywords": [
            "kepariwisataan", "cagar budaya", "ekonomi kreatif",
            "kesenian", "makam bersejarah", "sanggar",
            "kunjungan wisata", "wisatawan", "jasa pariwisata",
            "seniman", "kartu induk kesenian",
            "rekapitulasi kunjungan wisatawan", "obyek diduga cagar budaya",
            "penetapan cagar budaya",
        ],
    },
    {
        "name": "investment-sme",
        "description": "Investasi & UMKM",
        "keywords": [
            "investasi penanaman modal", "realisasi proyek penanaman modal",
            "penyertaan penanaman modal",
            "nomor induk berusaha", "nib oss",
            "koperasi yang mengikuti", "jumlah koperasi", "koperasi baru",
            "nilai omset koperasi", "nilai omset usaha mikro",
            "koperasi sehat", "usaha mikro naik kelas",
            "umkm", "wirausaha", "pameran umkm", "pirt",
            "nilai realisasi investasi", "jumlah bidang usaha",
            "tenaga kerja perusahaan", "sebaran proyek",
            "lama proses perizinan", "pertumbuhan realisasi investasi",
            "skala modal", "bentuk perusahaan",
            "bumdes", "pasar desa",
            "industri dan tenaga kerja", "perusahaan industri",
            "tera ulang timbangan", "pedagang pasar", "kondisi pasar",
            "sosialisasi dan pelatihan", "non perizinan",
        ],
    },
    {
        "name": "macro-economy",
        "description": "Ekonomi Makro",
        "keywords": [
            "pdrb", "inflasi", "tingkat kemiskinan", "garis kemiskinan",
            "tingkat pengangguran", "indeks gini",
            "indeks pembangunan manusia", "usia harapan hidup",
            "laju pertumbuhan ekonomi", "net ekspor", "pembentukan modal tetap",
            "spending of money", "indeks kebutuhan dasar",
            "kontribusi pdrb", "rasio pdrb",
            "persentase petumbuhan pdrb", "persentase pertumbuhan pdrb",
        ],
    },
    {
        "name": "infrastructure",
        "description": "Infrastruktur & Transportasi",
        "keywords": [
            "kondisi jalan", "kondisi jembatan", "bendung", "embung", "waduk",
            "saluran irigasi", "curah hujan", "penakar hujan", "hari hujan",
            "permukaan jalan", "rasio panjang jalan", "kesesuaian ruang",
            "wilayah perkotaan", "air bersih", "sanitasi",
            "layanan laboratorium dpupr",
            "data lalu lintas", "data angkutan umum",
            "petugas lalu lintas", "uji kendaraan",
        ],
    },
    {
        "name": "housing-settlement",
        "description": "Perumahan & Permukiman",
        "keywords": [
            "jumlah rumah", "rtlh", "rumah tidak layak huni", "backlog",
            "rumah susun", "site plan", "kawasan kumuh", "prasarana permukiman",
            "rumah layak huni", "permukiman kumuh", "pengelolaan tanah",
            "inventarisasi kawasan", "rlh",
        ],
    },
    {
        "name": "social-labor",
        "description": "Sosial & Ketenagakerjaan",
        "keywords": [
            "anak terlantar", "lansia terlantar", "kdrt", "orang dipasung",
            "disabilitas", "gelandangan", "bencana sosial",
            "pekerja sosial", "tagana", "pendamping pkh",
            "penerima manfaat pkh", "lembaga sosial",
            "karang taruna", "lembaga kesejahteraan anak",
            "karang werda", "penerima pbi", "dtks", "data kemiskinan",
            "pmks", "psks", "rehabilitasi disabilitas",
            "rehabilitasi gelandangan", "penanganan pmks", "penanganan psks",
            "penempatan tenaga kerja", "lembaga pelatihan kerja",
            "hubungan industrial", "transmigrasi",
            "partisipasi angkatan kerja perempuan",
            "kekerasan terhadap perempuan", "kabupaten layak anak",
            "sdm kesejahteraan", "wrse", "wanita tuna sosial",
            "korban bencana alam",
        ],
    },
    {
        "name": "environment",
        "description": "Lingkungan Hidup",
        "keywords": [
            "bank sampah", "desa berseri", "pengelolaan sampah",
            "tps3r", "armada pengelolaan sampah",
            "indeks kualitas lingkungan", "iklh",
            "flora dan fauna", "pencemaran",
            "persetujuan lingkungan", "limbah b3",
            "limbah padat", "limbah cair",
            "emisi grk", "jumlah tpa", "neraca pengelolaan sampah",
            "jumlah tps",
        ],
    },
    {
        "name": "disaster-security",
        "description": "Bencana & Keamanan",
        "keywords": [
            "tangguh bencana", "rawan bencana", "potensi relawan",
            "jumlah kejadian", "rumah terkena bencana",
            "layanan informasi rawan bencana", "kesiapsiagaan bencana",
            "penyelamatan dan evakuasi", "indeks risiko bencana",
            "kekeringan", "ketahanan daerah", "satuan pendidikan aman bencana",
            "pelanggaran perda", "acara yang diamankan",
            "kebakaran", "linmas", "konflik", "demonstrasi", "unjuk rasa",
            "penanganan kejadian", "ketertiban umum",
        ],
    },
    {
        "name": "governance",
        "description": "Tata Kelola Pemerintahan",
        "keywords": [
            # ASN / HR
            "pegawai berdasarkan", "jumlah asn", "asn baru", "asn pensiun",
            "pns mutasi", "asn berdasar", "indeks profesionalitas",
            "indeks sistem merit", "diklatpim",
            # DPRD
            "anggota dprd", "jumlah partai", "jumlah fraksi",
            "jumlah komisi", "indeks kepuasan dprd",
            # Reform / audit
            "reformasi birokrasi", "nilai sakip", "nilai lppd",
            "kecamatan dengan kinerja", "maturitas", "kapabilitas apip",
            "manajemen risiko indeks", "rekomendasi bpk",
            "indeks pelayanan publik",
            # Digital / IT
            "data wifi", "data aplikasi", "spbe",
            "kelompok informasi masyarakat", "media terferivikasi",
            "konten informasi kebijakan", "pengguna internet",
            "data statistik sektoral", "keamanan informasi",
            "jaringan intra pemerintah", "sistem penghubung layanan",
            "indeks masyarakat digital", "pengamanan informasi",
            "data dan produsen data", "evaluasi statistik",
            # Civil organizations
            "ormas binaan", "ormas berdasarkan", "ijin kkn",
            # Archives
            "jumlah arsip", "tata kelola kearsipan", "arsip elektronik",
            # Planning / indices
            "dokumen perencanaan", "keselarasan dokumen perencanaan",
            "indeks inovasi daerah", "indeks toleransi",
            "kualitas layanan infrastruktur", "indeks infrastruktur",
            # Village administration
            "profil desa", "status desa", "indeks membangun",
            "desa mandiri", "desa swasembada",
            "lembaga kemasyarakatan", "kerjasama pemerintah desa",
            "jumlah desa dan kelurahan",
            # Regional finance
            "realisasi pendapatan", "realisasi belanja", "realisasi pembiayaan",
            "pbb daerah", "laporan realisasi anggaran",
            # Misc
            "data pengaduan", "pkl",
            "swasembada", "dinas kominfo",
        ],
    },
]


def match(title: str, keywords: list[str]) -> bool:
    t = " ".join(title.lower().split())  # normalize whitespace
    for kw in keywords:
        k = kw.lower()
        if " " in k:
            if k in t:
                return True
        else:
            if re.search(r"\b" + re.escape(k) + r"\b", t):
                return True
    return False


def categorize(directories: dict) -> dict:
    buckets: dict[str, list] = {cat["name"]: [] for cat in CATEGORIES}
    uncategorized = []

    for dept in directories["items"]:
        for sub in dept["sub_items"]:
            entry = {
                "id": sub["id"],
                "title": sub["title"],
                "item_title": dept["title"],
            }
            assigned = False
            for cat in CATEGORIES:
                if match(sub["title"], cat["keywords"]):
                    buckets[cat["name"]].append(entry)
                    assigned = True
                    break
            if not assigned:
                uncategorized.append(entry)

    if uncategorized:
        logging.warning("%d item(s) could not be categorized:", len(uncategorized))
        for item in uncategorized:
            logging.warning("  [%s] %s", item["item_title"], item["title"])

    categories = [
        {
            "name": cat["name"],
            "description": cat["description"],
            "total_category_sub_items": len(buckets[cat["name"]]),
            "sub_items": buckets[cat["name"]],
        }
        for cat in CATEGORIES
    ]

    return {"total_categories": len(categories), "categories": categories}


def save_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not os.path.exists(INPUT_PATH):
        logging.error("Input not found: %s", INPUT_PATH)
        logging.error("Run scripts/extract_menu.py first.")
        sys.exit(1)

    with open(INPUT_PATH, encoding="utf-8") as f:
        directories = json.load(f)

    total_sub = sum(d["total_sub_items"] for d in directories["items"])
    logging.info(
        "Categorizing %d sub-items across %d departments...",
        total_sub,
        directories["total_items"],
    )

    result = categorize(directories)

    for cat in result["categories"]:
        logging.info("  %-32s %3d items", cat["name"], len(cat["sub_items"]))

    assigned = sum(len(cat["sub_items"]) for cat in result["categories"])
    logging.info("Total assigned: %d / %d", assigned, total_sub)

    save_json(result, OUTPUT_PATH)
    logging.info("Saved to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
