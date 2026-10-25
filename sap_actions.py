
import win32com.client
import json
from datetime import datetime, date, timedelta

#Átalakítjuk a mennyiséget számra
def parse_quantity(value):
    value = value.strip().replace(" ", "")
    negative = value.endswith("-")
    value = value.rstrip("-").replace(".", "").replace(",", ".")
    return -float(value) if negative else float(value or 0)

#Megnyitjuk a SAP GUI session-t
def get_session():
    sap_gui = win32com.client.GetObject("SAPGUI")
    app = sap_gui.GetScriptingEngine
    return app.Children(0).Children(0)

#Megnyitunk egy tranzakciót
def open_transaction(tcode):
    allowed = {"MM03", "VA03", "MD04"}

    if tcode not in allowed:
        raise ValueError(f"Nem engedélyezett tranzakció: {tcode}")

    session = get_session()
    session.StartTransaction(tcode)

    return f"{tcode} tranzakció elindítva"

#Megjelenítjük az MD04 tranzakciót és kiolvassuk az adatokat
def display_md04(material, plant):
    if not material or not plant:
        raise ValueError("Az anyagszám és a gyár kötelező!")
#Szelekció a tranzakcióban
    session = get_session()
    session.StartTransaction("MD04")
    session.findById("wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR").text = material
    session.findById("wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-WERKS").text = plant
    session.findById("wnd[0]").sendVKey(0)

#Kiolvasás a táblázatból
    # table_id = "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0750/tblSAPMM61RTC_EZ"
    # table = session.findById(table_id)

    # MD04 tábla automatikus keresése
    usr = session.findById("wnd[0]/usr")

    def find_table(parent):
        for i in range(parent.Children.Count):
            child = parent.Children(i)

            if child.Type == "GuiTableControl":
                print("Megtalált tábla:", child.Id)
                return child

            try:
                found = find_table(child)
                if found:
                    return found
            except Exception:
                pass

        return None

    table = find_table(usr)

    if table is None:
        raise RuntimeError("Nem található MD04 táblázat!")

    table_id = table.Id

    total = table.RowCount
    visible = table.VisibleRowCount

    data = []
    processed = set()

#Megnézzük az összes sorát a táblázatnak, és kiolvassuk az adatokat
    for start in range(0, total, visible):
        table = session.findById(table_id)
        table.verticalScrollbar.position = start
        table = session.findById(table_id)
        actual = table.verticalScrollbar.position
        for r in range(visible):
            absolute_row = actual + r
            if absolute_row >= total or absolute_row in processed:
                continue
            record = {"row": absolute_row}
            for col in [1, 2, 5, 8, 9]:
                try:
                    record[col] = table.GetCell(r, col).Text.strip()
                except Exception:
                    record[col] = ""
            processed.add(absolute_row)
            if record[2]:
                data.append(record)

    records = []

#Első oszlop a dátum, második az MRP elem, harmadik a hivatkozás, negyedik a mennyiség, ötödik az elérhető mennyiség
    for item in data:
        records.append({
            "date": datetime.strptime(
                item[1], "%d.%m.%Y"
            ).strftime("%Y-%m-%d"),
            "mrp_element": item[2],
            "reference": item[5],
            "quantity": parse_quantity(item[8]),
            "available": parse_quantity(item[9])
        })

    result = {
        "material": material,
        "plant": plant,
        "records": records
    }

    return result

#Összesítjük az MD04 adatait

def summarize_md04(result, period="all"):
    all_records = result["records"]
    records = all_records.copy()

    start = None
    end = None

    # Időszak meghatározása
    if period == "next_week":
        today = date.today()
        start = today + timedelta(days=7 - today.weekday())
        end = start + timedelta(days=6)

    elif period != "all":
        raise ValueError(f"Nem támogatott időszak: {period}")

    # Időszakra vonatkozó rekordok szűrése
    if start is not None:
        records = [
            r for r in all_records
            if start <= date.fromisoformat(r["date"]) <= end
        ]

    # Nyitó rendelkezésre álló mennyiség
    if start is not None:
        previous = [
            r for r in all_records
            if date.fromisoformat(r["date"]) < start
        ]
        opening_stock = previous[-1]["available"] if previous else None
    else:
        opening_stock = next(
            (r["available"] for r in all_records
             if r["mrp_element"] == "Stock"),
            None
        )

    # Igények összesítése
    demand = sum(
        abs(r["quantity"])
        for r in records
        if r["quantity"] < 0 and r["mrp_element"] != "Stock"
    )

    # Beérkezések összesítése
    receipts = sum(
        r["quantity"]
        for r in records
        if r["quantity"] > 0 and r["mrp_element"] != "Stock"
    )

    # Záró tervezett rendelkezésre álló mennyiség
    closing_available = (
        records[-1]["available"]
        if records else opening_stock
    )

    # Minimum rendelkezésre álló mennyiség
    available_values = [
        r["available"] for r in records
    ]

    if opening_stock is not None:
        available_values.insert(0, opening_stock)

    minimum_available = (
        min(available_values) if available_values else None
    )

    # Negatív rendelkezésre álló mennyiség keresése
    shortage_records = [
        {
            "date": r["date"],
            "available": r["available"]
        }
        for r in records
        if r["available"] < 0
    ]

    shortage_detected = (
        minimum_available < 0
        if minimum_available is not None else None
    )

    return {
        "material": result["material"],
        "plant": result["plant"],
        "period": period,
        "period_start": start.isoformat() if start else None,
        "period_end": end.isoformat() if end else None,
        "opening_stock": opening_stock,
        "total_demand": demand,
        "total_receipts": receipts,
        "closing_available": closing_available,
        "minimum_available": minimum_available,
        "shortage_detected": shortage_detected,
        "shortage_dates": sorted(set(
            r["date"] for r in shortage_records
        ))
    }


#Teszteléshez
if __name__ == "__main__":
    result = display_md04("ZPDS-MOTOR-A", "2140")
    summary = summarize_md04(result)

    print(json.dumps(summary, indent=2, ensure_ascii=False))

