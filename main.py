import json
import math
from colored import Back, Style
from prettytable import PrettyTable


class Composition:
    WAKTU_SLICE = {"pagi-top": slice(0, 4), "pagi-bottom": slice(4, 8), "siang-top": slice(8, 12), "siang-bottom": slice(12, 16), "sore-top": slice(16, 20), "sore-bottom": slice(20, 24)}

    def __init__(self, filename: str = "data.json"):
        with open(filename, "r") as f:
            self.simpang = json.load(f)

    def calculate(self):
        result = []
        for i in self.simpang:
            temp = {}
            for ke, value_ke in i["ke"].items():
                temp[ke] = {
                    "pagi": {"mc": 0, "lv": 0, "hv": 0, "um": 0},
                    "siang": {"mc": 0, "lv": 0, "hv": 0, "um": 0},
                    "sore": {"mc": 0, "lv": 0, "hv": 0, "um": 0},
                }
                highest_traffic = []
                for k, v in enumerate(["pagi", "siang", "sore"]):
                    sl = [slice(0, 8), slice(8, 16), slice(16, 24)]
                    top = 0
                    bottom = 0
                    for j in self.simpang:
                        for l in j["ke"][ke]:
                            top += sum(l["data"][sl[k]][0:4])
                            bottom += sum(l["data"][sl[k]][4:8])
                    if top >= bottom:
                        highest_traffic.append(v + "-top")
                    else:
                        highest_traffic.append(v + "-bottom")

                for high in highest_traffic:
                    for j in value_ke:
                        waktu = high.split("-")[0]
                        temp[ke][waktu][j["jenis"]] += sum(j["data"][self.WAKTU_SLICE[high]])

            result.append(i | {"composition": temp})

        return result


class PeakHour:
    Convention = {
        "mc": 0.5,
        "lv": 1,
        "hv": 1.2,
        "um": 0,
    }

    def __init__(self, composition) -> None:
        self.composition = composition

    def create_smp(self):
        for idx, i in enumerate(self.composition):
            olah_data = {
                "pagi": {"lurus": {}, "kanan": {}, "kiri": {}},
                "siang": {"lurus": {}, "kanan": {}, "kiri": {}},
                "sore": {"lurus": {}, "kanan": {}, "kiri": {}},
            }
            for j in i["composition"]:
                for k in i["composition"][j]:
                    olah_data[k][j] = {
                        "mc": round(i["composition"][j][k]["mc"] * self.Convention["mc"], 4),
                        "lv": round(i["composition"][j][k]["lv"] * self.Convention["lv"], 4),
                        "hv": round(i["composition"][j][k]["hv"] * self.Convention["hv"], 4),
                        "um": round(i["composition"][j][k]["um"] * self.Convention["um"], 4),
                    }
            self.composition[idx]["smp"] = olah_data

    def create_Q(self):
        Q_smp = {
            "pagi": 0,
            "siang": 0,
            "sore": 0,
        }
        QLT = Q_smp.copy()
        QRT = Q_smp.copy()
        Q = Q_smp.copy()
        Qma = Q_smp.copy()
        Qmi = Q_smp.copy()
        for i in self.composition:
            for j in i["smp"]:
                for k in i["smp"][j]:
                    Q_smp[j] += sum(i["smp"][j][k].values())

        for i in self.composition:
            for j in i["composition"]:
                for k in i["composition"][j]:
                    if j == "kiri":
                        QLT[k] += sum(i["composition"][j][k].values())
                    if j == "kanan":
                        QRT[k] += sum(i["composition"][j][k].values())
                    Q[k] += sum(i["composition"][j][k].values())
                    if "minor" in i["tipe"]:
                        Qmi[k] += sum(i["composition"][j][k].values())
                    if "utama" in i["tipe"]:
                        Qma[k] += sum(i["composition"][j][k].values())

        return [Q, QLT, QRT, Qmi, Qma, Q_smp]


class Capacity:
    KAPASITAS_DASAR = {
        "322": 2700,
        "342": 2900,
        "324": 3200,
        "344": 3200,
        "422": 2900,
        "424": 3400,
        "444": 3400,
    }

    PENYESUAIAN_LEBAR_PENDEKAT = {
        "322": lambda W1: 0.73 + 0.0760 * W1,
        "342": lambda W1: 0.67 + 0.0698 * W1,
        "324": lambda W1: 0.62 + 0.0646 * W1,
        "344": lambda W1: 0.62 + 0.0646 * W1,
        "422": lambda W1: 0.70 + 0.0866 * W1,
        "424": lambda W1: 0.61 + 0.0740 * W1,
        "444": lambda W1: 0.61 + 0.0740 * W1,
    }

    FAKTOR_PENYESUAIAN_MEDIAN = {"tidak-ada": 1.00, "sempit": 1.05, "lebar": 1.20}
    FAKTOR_PENYESUAIAN_UKURAN_KOTA = {"sangat-kecil": 0.82, "kecil": 0.88, "sedang": 0.94, "besar": 1.00, "sangat-besar": 1.05}
    FRSU = 0.88
    FAKTOR_PENYESUAIAN_ARUS_JALAN_MINOR = {
        "422": lambda x: 1.19 * x**2 - 1.19 * x + 1.19,
    }

    def __init__(self, data) -> None:
        self.data = data
        pass

    def lebar_rata_rata_pendekat(self):
        def median_check(x):
            if x["median"]:
                return x["lebar_lajur"]
            else:
                return x["lebar_lajur"] / 2

        total_lebar = list(filter(lambda x: x, map(median_check, self.data)))
        return sum(total_lebar) / len(total_lebar)

    def lebar_rata_rata_pendekat_minor_utama(self):
        def minor_check(x):
            if "minor" in x["tipe"]:
                if x["median"]:
                    return x["lebar_lajur"]
                else:
                    return x["lebar_lajur"] / 2

        def utama_check(x):
            if "utama" in x["tipe"]:
                if x["median"]:
                    return x["lebar_lajur"]
                else:
                    return x["lebar_lajur"] / 2

        total_lebar_minor = list(filter(lambda x: x, map(minor_check, self.data)))
        total_lebar_utama = list(filter(lambda x: x, map(utama_check, self.data)))
        return round(sum(total_lebar_minor) / len(total_lebar_minor), 2), round(sum(total_lebar_utama) / len(total_lebar_utama), 2)

    def jumlah_lajur(self):
        minor, utama = self.lebar_rata_rata_pendekat_minor_utama()
        result = []
        if minor < 5.5:
            result.append(2)
        elif minor > 5.5:
            result.append(4)

        if utama < 5.5:
            result.append(2)
        elif utama > 5.5:
            result.append(4)

        return result

    def tipe_simpang(self):
        return "".join(map(lambda x: str(x), [len(self.data)] + self.jumlah_lajur()))

    def kapasitas_dasar(self):
        return self.KAPASITAS_DASAR[self.tipe_simpang()]

    def faktor_penyesuaian_lebar_pendekat(self):
        return self.PENYESUAIAN_LEBAR_PENDEKAT[self.tipe_simpang()](self.lebar_rata_rata_pendekat())

    def faktor_penyesuaian_median_jalan_utama(self):
        def utama_check(x):
            if "utama" in x["tipe"]:
                if not x["median"]:
                    return self.FAKTOR_PENYESUAIAN_MEDIAN["tidak-ada"]
                elif x["median"] < 3:
                    return self.FAKTOR_PENYESUAIAN_MEDIAN["sempit"]
                elif x["median"] >= 3:
                    return self.FAKTOR_PENYESUAIAN_MEDIAN["lebar"]

        return list(map(utama_check, self.data))[0]

    def faktor_penyesuaian_ukuran_kota(self):
        return self.FAKTOR_PENYESUAIAN_UKURAN_KOTA["sedang"]

    def frsu(self):
        return self.FRSU

    def faktor_penyesuaian_belok(self, Q, QLT, QRT):
        PLT = QLT / Q
        FLT = 0.84 + 1.61 * PLT
        PRT = QRT / Q
        FRT = 0.84 + 1.61 * PRT
        if len(self.data) == 4:
            FRT = 1
        return FLT, FRT

    def faktor_penyesuaian_rasio_arus_jalan_minor(self, Q, Qmi):
        return self.FAKTOR_PENYESUAIAN_ARUS_JALAN_MINOR[self.tipe_simpang()](Qmi / Q)

    def capacity(self, Q, QLT, QRT, Qmi):
        C = (
            self.kapasitas_dasar()
            * self.faktor_penyesuaian_lebar_pendekat()
            * self.faktor_penyesuaian_median_jalan_utama()
            * self.faktor_penyesuaian_ukuran_kota()
            * self.frsu()
            * self.faktor_penyesuaian_belok(Q, QLT, QRT)[0]
            * self.faktor_penyesuaian_belok(Q, QLT, QRT)[1]
            * self.faktor_penyesuaian_rasio_arus_jalan_minor(Q, Qmi)
        )
        return C


def printRoman(number):
    str = ""
    num = [1, 4]
    sym = ["I", "IV"]
    i = 1

    while number:
        div = number // num[i]
        number %= num[i]

        while div:
            str += sym[i]
            div -= 1
        i -= 1
    return str


def create_siklus_waktu(fase, add_row):
    IG = 4
    AR = 1
    AMBER = 3
    gi = 0

    FRe = sum(map(lambda x: x["fr"], fase))
    LTI = IG * len(fase)

    merah_prev = 0
    result = []
    for idx, i in enumerate(fase):
        S = i["S"]
        Q2 = i["fr"] * S

        if idx > 0:
            merah_prev += gi + AR + AMBER

        c = math.ceil((1.5 * LTI + 5) / (1 - FRe))  # SIKLUS
        gi = math.ceil((c - LTI) * (i["fr"] / FRe))  # HIJAU
        C2 = S * (gi / c)  # kapasitas
        DS = Q2 / C2

        merah_prevv2 = merah_prev - (1 if idx else 0)
        hijau = gi
        kuning = AMBER
        all_red = AR
        merah_next = c - gi - AMBER - merah_prev - (1 if idx == 0 else 0)

        tmerah_prevv2 = merah_prevv2 if merah_prevv2 else ""
        tmerah_next = merah_next if merah_next else ""
        add_row(
            [
                str(len(fase)) + " Fase",
                c,
                IG,
                len(fase),
                AMBER,
                AR,
                LTI,
                i["pendekat"],
                gi,
                c - gi - AMBER,
                round(C2, 2),
                round(DS, 2),
                printRoman(idx + 1),
                f"{Back.RED}{f'{tmerah_prevv2}'.center(merah_prevv2)}{Back.GREEN}{f'{hijau}'.center(hijau)}{Back.YELLOW}{f'{kuning}'.center(kuning)}{Back.RED}{f'{all_red}'.center(all_red)}{f'{tmerah_next}'.center(merah_next) }{Style.reset}",
            ],
            divider=True if idx == len(fase) - 1 else False,
        )
    return result


def level_of_service(DS):
    if DS <= 0.02:
        return "A"
    elif DS <= 0.44:
        return "B"
    elif DS <= 0.74:
        return "C"
    elif DS <= 0.84:
        return "D"
    elif DS < 1.00:
        return "E"
    else:
        return "F"


def main():
    composition = Composition()
    peak_hour = PeakHour(composition.calculate())
    peak_hour.create_smp()

    capacity = Capacity(peak_hour.composition)

    Q, QLT, QRT, Qmi, Qma, Q_smp = peak_hour.create_Q()
    rekapitulasi = {}

    for v in ["pagi", "siang", "sore"]:
        C = round(capacity.capacity(Q[v], QLT[v], QRT[v], Qmi[v]), 2)
        DS = round(round(Q_smp[v], 2) / C, 2)
        if DS <= 0.6:
            DT1 = 2 + 8.2078 * DS - (1 - DS) * 2
            DTma = 1.8 + 5.8234 * DS - (1 - DS) * 1.8
        elif DS > 0.6:
            DT1 = 1.0504 / (0.2742 - 0.2042 * DS) - (1 - DS) * 2
            DTma = 1.05034 / (0.346 - 0.246 * DS) - (1 - DS) * 1.8
        DTmi = round((Q[v] * DT1 - Qma[v] * DTma) / Qmi[v], 2)
        PT = round((QLT[v] + QRT[v]) / Q[v], 2)
        if DS < 1.0:
            DG = (1 - DS) * (PT * 6 + (1 - PT) * 3) + DS * 4
        else:
            DG = 4

        D = round(DT1 + DG, 2)
        rekapitulasi[v] = {
            "Q": Q[v],
            "C": C,
            "DS": DS,
            "D": D,
        }

    rekapitulasi = list(rekapitulasi.items())
    rekapitulasi.sort(key=lambda x: x[1]["D"], reverse=True)

    SELECTED = rekapitulasi[0][0]
    rekap_ds = PrettyTable()
    rekap_ds.field_names = ["Jam Sibuk", "Derajat Kejenuhan (DS)", "Level Of Service (LOS)"]
    for i in rekapitulasi:
        if i[0] == SELECTED:
            rekap_ds.add_row([f"{Back.RED}{i[0]}{Style.RESET_ALL}", f"{Back.RED}{i[1]['DS']}{Style.RESET_ALL}", f"{Back.RED}{level_of_service(i[1]['DS'])}{Style.RESET_ALL}"])
        else:
            rekap_ds.add_row([i[0], i[1]["DS"], level_of_service(i[1]["DS"])])

    print(rekap_ds)

    high_ds = PrettyTable()
    high_ds.field_names = ["Deskripsi Level Of Service  (LOS)"]
    high_ds.align["Deskripsi Level Of Service  (LOS)"] = "l"
    with open("level_of_service.json", "r") as f:
        i = json.load(f)
        for j in i[level_of_service(rekapitulasi[0][1]["DS"])]:
            high_ds.add_row([j])
    print(high_ds)

    MERGE_SELECTED = []

    for i in peak_hour.composition:
        QLV = i["smp"][SELECTED]["lurus"]["lv"] + i["smp"][SELECTED]["kanan"]["lv"] + i["smp"][SELECTED]["kiri"]["lv"]
        QHV = i["smp"][SELECTED]["lurus"]["hv"] + i["smp"][SELECTED]["kanan"]["hv"] + i["smp"][SELECTED]["kiri"]["hv"]
        QMC = i["smp"][SELECTED]["lurus"]["mc"] + i["smp"][SELECTED]["kanan"]["mc"] + i["smp"][SELECTED]["kiri"]["mc"]
        empHV = 1.3
        empMC = 0.4
        Q2 = QLV + QHV * empHV + QMC * empMC
        S = i["lebar_lajur"] * 600
        data = {
            "arah": i["arah"],
            "tipe": i["tipe"],
            "lebar_lajur": i["lebar_lajur"],
            "pendekat": i["pendekat"],
            "Q": round(Q2, 2),
            "S": S,
        }

        MERGE_SELECTED.append(data)

    result = PrettyTable()

    result.field_names = ["Recom Fase", "Siklus", "IG", "F", "Amber", "AR", "LTI", "Pendekat", "Hijau", "Merah", "Kapasitas", "DS", "Fase", "Siklus Waktu"]

    fase = []
    for i in MERGE_SELECTED:
        fase.append(i | {"fr": round(i["Q"] / i["S"], 3)})

    create_siklus_waktu(fase, result.add_row)

    fase2 = []
    max_utama = max(list(filter(lambda x: "utama" in x["tipe"], fase)), key=lambda x: x["fr"]).copy()
    max_utama["pendekat"] = "US"
    fase2.append(max_utama)
    fase2 += list(filter(lambda x: "minor" in x["tipe"], fase))

    create_siklus_waktu(fase2, result.add_row)

    fase3 = []
    max_minor = max(list(filter(lambda x: "minor" in x["tipe"], fase)), key=lambda x: x["fr"]).copy()
    max_minor["pendekat"] = "BT"
    fase3 += list(filter(lambda x: "utama" in x["tipe"], fase))
    fase3.insert(1, max_minor)

    create_siklus_waktu(fase3, result.add_row)

    fase4 = []
    max_utama = max(list(filter(lambda x: "utama" in x["tipe"], fase)), key=lambda x: x["fr"]).copy()
    max_utama["pendekat"] = "US"
    max_minor = max(list(filter(lambda x: "minor" in x["tipe"], fase)), key=lambda x: x["fr"]).copy()
    max_minor["pendekat"] = "BT"
    fase4 += [max_utama, max_minor]

    create_siklus_waktu(fase4, result.add_row)
    print(result)


if __name__ == "__main__":
    main()
