# Use Case Specification - Purifyt

Sistem deteksi & penghapusan komentar judi online pada YouTube.

**Aktor:**
- **Guest** — pengunjung yang belum terautentikasi.
- **Registered User** — pengguna yang sudah login (memiliki access token).

**Sistem Eksternal:** YouTube Data API, YouTube Studio, Kaggle, ML Model.

---

## UC-01 Login

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-01 |
| **Use Case Name** | Login |
| **Aktor** | Guest |
| **Deskripsi** | Mengautentikasi pengguna menggunakan email/username dan password, menghasilkan access token (JWT) dan refresh token (HttpOnly cookie). |
| **Prakondisi** | Pengguna sudah memiliki akun terdaftar. |
| **Paskondisi** | Access token diterbitkan, refresh token tersimpan di DB dan dikirim sebagai cookie. |
| **Trigger** | Pengguna mengirim kredensial melalui `POST /api/v1/auth/login`. |
| **Alur Utama** | 1. Pengguna memasukkan email/username + password.<br>2. Sistem mencari user berdasarkan email/username.<br>3. Sistem memverifikasi password (hash).<br>4. Sistem membuat access token + refresh token.<br>5. Sistem menyimpan refresh token & set cookie.<br>6. Sistem mengembalikan access token. |
| **Alur Alternatif** | 2a/3a. Kredensial salah → sistem mengembalikan `401 Incorrect credentials`.<br>1a. Email/username tidak diisi → `400 Provide email or username`. |
| **Exception** | Kegagalan koneksi database. |

---

## UC-02 Register

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-02 |
| **Use Case Name** | Register |
| **Aktor** | Guest |
| **Deskripsi** | Mendaftarkan akun baru dengan username, email, dan password. |
| **Prakondisi** | Username dan email belum terdaftar. |
| **Paskondisi** | Akun baru tersimpan di database dengan password ter-hash. |
| **Trigger** | `POST /api/v1/auth/register`. |
| **Alur Utama** | 1. Pengguna mengisi username, email, password.<br>2. Sistem memvalidasi keunikan username.<br>3. Sistem memvalidasi keunikan email.<br>4. Sistem meng-hash password.<br>5. Sistem menyimpan user baru.<br>6. Sistem mengembalikan data user (201). |
| **Alur Alternatif** | 2a. Username sudah ada → `400 Username already exists`.<br>3a. Email sudah terdaftar → `400 Email already registered`. |
| **Exception** | Kegagalan koneksi database. |

---

## UC-03 Manage Profile

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-03 |
| **Use Case Name** | Manage Profile |
| **Aktor** | Registered User |
| **Deskripsi** | Mengelola sesi & profil: melihat profil sendiri, refresh token, logout, serta melihat daftar/detail user. |
| **Prakondisi** | Pengguna sudah login (memiliki access token / refresh cookie valid). |
| **Paskondisi** | Profil ditampilkan; atau token diperbarui; atau sesi diakhiri. |
| **Trigger** | `GET /auth/me`, `POST /auth/refresh`, `POST /auth/logout`, `GET /users`, `GET /users/{id}`. |
| **Alur Utama** | 1. Pengguna meminta data profil (`/auth/me`).<br>2. Sistem memvalidasi access token.<br>3. Sistem mengembalikan data profil.<br>4. (Refresh) Sistem menukar refresh cookie dengan token baru & merotasi token lama.<br>5. (Logout) Sistem mencabut refresh token & menghapus cookie. |
| **Alur Alternatif** | 2a. Token tidak valid/kadaluarsa → `401 Unauthorized`.<br>4a. Refresh token hilang/invalid → `401`, cookie dibersihkan.<br>5a. User detail tidak ditemukan → `404 User not found`. |
| **Exception** | Kegagalan koneksi database. |

---

## UC-04 Manage Dataset

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-04 |
| **Use Case Name** | Manage Dataset |
| **Aktor** | Registered User |
| **Deskripsi** | Mengelola dataset komentar: membuat dataset dari sumber (YouTube/Kaggle), melihat daftar & detail, mencari komentar, dan menghapus dataset. |
| **Prakondisi** | Pengguna sudah login. |
| **Paskondisi** | Dataset terbentuk/terhapus, atau data komentar ditampilkan. |
| **Trigger** | `GET/DELETE /datasets`, `GET /datasets/{id}`, `GET /datasets/{id}/comments`, `GET /datasets/search/comments`, `POST /youtube/import`, `GET/POST /kaggle/import`. |
| **Alur Utama** | 1. Pengguna meminta daftar dataset (dengan paginasi & filter sumber).<br>2. Sistem mengambil dataset beserta jumlah komentar.<br>3. Pengguna membuka detail dataset / daftar komentar / pencarian.<br>4. Pengguna mengimpor data dari YouTube atau Kaggle (membuat dataset baru + bulk insert komentar).<br>5. Pengguna menghapus dataset bila perlu. |
| **Alur Alternatif** | 3a. Dataset tidak ditemukan → `404 Dataset not found`.<br>4a. Tidak ada komentar/baris dapat di-parse → `400/404`.<br>5a. Dataset yang dihapus tidak ada → `404`. |
| **Include** | Import YouTube meng-`include` Search YouTube; Import Kaggle berinteraksi dengan sistem Kaggle. |
| **Exception** | Kegagalan API eksternal (YouTube/Kaggle) atau database. |

---

## UC-05 Predict Comments

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-05 |
| **Use Case Name** | Predict Comments |
| **Aktor** | Registered User |
| **Sistem Eksternal** | ML Model |
| **Deskripsi** | Memprediksi label komentar (0 = non judi, 1 = judi online) secara satuan, batch, auto-label dataset, serta koreksi label manual. |
| **Prakondisi** | Pengguna sudah login; model ML tersedia. |
| **Paskondisi** | Komentar memiliki `predicted_label`/`clean_comment`; atau label manual terkoreksi. |
| **Trigger** | `POST /labeling/predict`, `/predict/batch`, `/dataset/{id}`, `PATCH /comment/{id}`, `PATCH /dataset/{id}/bulk`, `DELETE /comment/{id}/label`, `POST /youtube/scan`. |
| **Alur Utama** | 1. Pengguna mengirim teks atau memilih dataset.<br>2. Sistem membersihkan teks (text cleaner).<br>3. Sistem menjalankan model prediksi.<br>4. Sistem menyimpan/ mengembalikan label + skor confidence.<br>5. (Manual) Pengguna mengoreksi label yang salah (false positive/negative), satuan atau bulk. |
| **Alur Alternatif** | 3a. Model gagal dimuat → `500`.<br>1a. Dataset tanpa komentar → `404 No comments found`.<br>5a. Comment tidak ditemukan → `404 Comment not found`. |
| **Exception** | Model belum termuat / file model hilang. |

---

## UC-06 Manage Cookie YouTube Accounts

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-06 |
| **Use Case Name** | Manage Cookie YouTube Accounts |
| **Aktor** | Registered User |
| **Sistem Eksternal** | YouTube Studio (Google Login) |
| **Deskripsi** | Mengelola akun cookie Google/YouTube Studio: login otomatis untuk menyimpan cookie, melihat daftar/detail cookie, dan menghapus akun cookie. |
| **Prakondisi** | Pengguna sudah login ke Purifyt. |
| **Paskondisi** | Cookie YouTube Studio tersimpan per email & tercatat di database; atau dihapus. |
| **Trigger** | `POST /auto-delete/login`, `GET /auto-delete/cookies`, `GET /auto-delete/cookies/{email}`, `DELETE /auto-delete/cookies/{email}`. |
| **Alur Utama** | 1. Pengguna mengirim email & password akun Google.<br>2. Sistem menjalankan browser otomatis dan mengisi form login.<br>3. Sistem menyimpan cookie ke folder per-email & mencatat path di DB.<br>4. Sistem mengirim progres via SSE (status, done, error).<br>5. Pengguna dapat melihat daftar/detail atau menghapus akun cookie. |
| **Alur Alternatif** | 2a. Login gagal/timeout → event `error`.<br>5a. Cookie untuk email tidak ditemukan → pesan error. |
| **Exception** | Kegagalan browser otomatis / verifikasi Google. |

---

## UC-07 Delete Gambling Comments

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-07 |
| **Use Case Name** | Delete Gambling Comments |
| **Aktor** | Registered User |
| **Sistem Eksternal** | YouTube Studio, ML Model |
| **Deskripsi** | Memindai komentar suatu video dan menghapus komentar yang terdeteksi judi; mendukung preview (dry-run), hapus spesifik berdasarkan comment ID, dan fetch komentar. |
| **Prakondisi** | Cookie akun (email) sudah tersimpan (lihat UC-06). |
| **Paskondisi** | Komentar judi terhapus dari YouTube Studio; hasil dilaporkan via SSE. |
| **Trigger** | `POST /auto-delete/scan`, `/scan/preview`, `/delete`, `/comments`. |
| **Alur Utama** | 1. Pengguna mengirim `video_id`, `email`, `threshold`.<br>2. Sistem memulai browser dengan cookie tersimpan.<br>3. Sistem mengambil komentar video dari YouTube Studio.<br>4. Sistem menjalankan deteksi judi (model).<br>5. Sistem menghapus komentar yang melewati threshold.<br>6. Sistem mengirim event SSE (status, judi_detected, delete, done). |
| **Alur Alternatif** | 2a. Cookie tidak ditemukan → event `error` (arahkan ke login).<br>Preview: langkah 5 dilewati (dry-run).<br>Delete spesifik: hapus hanya `comment_ids` yang dikirim. |
| **Include** | Scan & Delete meng-`include` Fetch Comments dan Predict (ML Model). |
| **Exception** | Browser gagal start / sesi YouTube Studio invalid. |

---

## UC-08 Explore Video

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-08 |
| **Use Case Name** | Explore Video |
| **Aktor** | Registered User |
| **Sistem Eksternal** | YouTube Data API, ML Model |
| **Deskripsi** | Menjelajahi satu video YouTube: mengambil seluruh komentar, melabeli dengan model, dan (opsional) menyimpan komentar judi + sampel normal ke dataset. Progres real-time via SSE. |
| **Prakondisi** | Pengguna sudah login; `video_id` valid. |
| **Paskondisi** | Statistik judi/normal ditampilkan; bila `dataset_name` diisi, komentar tersimpan ke dataset baru. |
| **Trigger** | `POST /explorer/run`. |
| **Alur Utama** | 1. Pengguna mengirim `video_id` (+ opsional `dataset_name`).<br>2. Sistem mengambil info video & seluruh komentar.<br>3. Sistem melabeli komentar batch-per-batch (streaming).<br>4. Jika ada judi & `dataset_name` diisi → simpan semua judi + (judi × 1.5) normal.<br>5. Sistem mengirim event `complete` dengan dataset & statistik. |
| **Alur Alternatif** | 4a. 0 judi → tidak disimpan, info dikembalikan.<br>4b. `dataset_name` kosong → mode scan-only, tidak disimpan.<br>2a. Gagal fetch → event `error`. |
| **Include** | Meng-`include` Predict (ML Model). |
| **Exception** | Kegagalan YouTube API / database. |

---

## UC-09 Explore Channel

| Field | Keterangan |
|---|---|
| **Use Case ID** | UC-09 |
| **Use Case Name** | Explore Channel |
| **Aktor** | Registered User |
| **Sistem Eksternal** | YouTube Data API, ML Model |
| **Deskripsi** | Menjelajahi sebuah channel YouTube (@handle atau channel ID): mengambil video terbaru, memproses komentar tiap video, dan menyimpan video yang mengandung judi ke dataset. Progres real-time via SSE. |
| **Prakondisi** | Pengguna sudah login; channel valid. |
| **Paskondisi** | Statistik agregat ditampilkan; bila `dataset_name` diisi, komentar video ber-judi tersimpan. |
| **Trigger** | `POST /explorer/channel/run`. |
| **Alur Utama** | 1. Pengguna mengirim `channel`, `max_videos` (+ opsional `dataset_name`).<br>2. Sistem me-resolve info channel.<br>3. Sistem mengambil daftar video terbaru.<br>4. Untuk tiap video: ambil komentar, labeli per batch.<br>5. Bila video punya judi → simpan langsung ke dataset.<br>6. Sistem mengirim event `complete` dengan statistik agregat. |
| **Alur Alternatif** | 4a. Video error/tanpa komentar → `video_skip`.<br>5a. `dataset_name` kosong → mode scan-only, tidak disimpan.<br>2a. Channel tidak ditemukan → event `error`. |
| **Include** | Meng-`include` Predict (ML Model). |
| **Exception** | Kegagalan YouTube API / database. |
