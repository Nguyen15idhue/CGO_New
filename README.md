# USB Guard cho CHC Geomatics Office 2

## Tinh nang

- ✅ Bao mat USB: Kich hoat bang key, chi USB cua ban moi chay duoc
- ✅ Dongle ao: Cam USB vao may nao cung chay duoc
- ✅ Tu dong phuc hoi: Rut USB ra thi phan mem dong lai va phuc hoi file goc
- ✅ Bao mat: Khong can cai dat them phan mem nao
- ✅ An toan: ID may duoc ma hoa, khong hien thi ra ngoai

## Cau truc file tren USB

```
USB/
├── CHC Geomatics Office 2.exe   # File chinh (da bao gom DLL)
└── README.md                     # Huong dan
```

## Huong dan su dung

### Buoc 1: Kich hoat (chi lam 1 lan tren may moi)

1. Cam USB vao may
2. Double-click `CHC Geomatics Office 2.exe`
3. Se hien thi cua so kich hoat voi **Ma (an)**
4. **Gui ma nay cho nguoi cung cap** de lay key kich hoat
5. Nhap **Key Kich Hoat** (dang CHC-XXXX-XXXX-XXXX) va bam "Kich Hoat"
6. Neu key dung, phan mem se khoi dong

### Buoc 2: Su dung phan mem

Sau khi da kich hoat:
1. Cam USB vao may
2. Double-click `CHC Geomatics Office 2.exe`
3. Phan mem se khoi dong ngay (khong can nhap key nua)

### Buoc 3: Rut USB

- Rut USB ra khi phan mem dang chay:
  - Phan mem bi dong ngay lap tuc
  - File DLL goc duoc phuc hoi tu dong

## Cach tao key cho khach hang (Admin)

1. **Khach hang gui ma** (tu phan mem) cho ban
2. **Chay file `KeyGen.exe`** (chi admin co)
3. **Nhap ma cua khach hang** vao o "Nhap Ma"
4. Bam "Tao Key" -> hien thi **Key Kich Hoat**
5. **Gui key nay cho khach hang**

## Luu y

- **1 key = 1 may:** Moi key chi su dung duoc tren 1 may
- **License luu tai:** Thong tin license luu tai `%APPDATA%\CHCNAV\CHC Geomatics Office 2\license.dat`
- **Cai dat lai may:** Neu cai lai Windows, can kich hoat lai

## Huong dan phan phoi

### De phan phoi cho khach hang:

1. **File can copy vao USB:**
   - `CHC Geomatics Office 2.exe` (file chinh)
   - `README.md` (huong dan su dung, tuy chon)

2. **Khong can kem them:**
   - KeyGen.exe (chi admin su dung, khong can phat cho khach)

3. **Quy trinh:**
   - Khach hang chay phan mem, gui ma cho admin
   - Admin chay KeyGen, nhap ma -> tao key
   - Admin gui key lai cho khach
   - Khach nhap key de kich hoat lan dau

## Xoa license (neu can)

Xoa file `%APPDATA%\CHCNAV\CHC Geomatics Office 2\license.dat` de kich hoat lai.

## Thong tin ky thuat

- **Ngon ngu:** Python 3
- **Cong cu dong goi:** PyInstaller
- **Dung luong:** ~11 MB
- **He thong:** Windows 7/10/11
