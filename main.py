import flet as ft
import pandas as pd
import os

def load_data(filename):
    try:
        # Cerchiamo il file nella cartella locale
        if os.path.exists(filename):
            df = pd.read_csv(filename, sep=';', header=None, skiprows=2, encoding='utf-8-sig')
            df.set_index(0, inplace=True)
            res_list = ['0-0', '1-0', '0-1', '1-1', '2-0', '0-2', '3-0', '0-3', '2-1', '1-2', '3-1', '1-3', '2-2']
            df.columns = [f"PUNTA_{r}" for r in res_list] + [f"BANCA_{r}" for r in res_list]
            for col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            return df
    except Exception as e:
        print(f"Errore caricamento: {e}")
    return None

def main(page: ft.Page):
    page.title = "TYPO HT-PRO MOBILE"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0e14"
    page.scroll = ft.ScrollMode.AUTO 
    page.padding = 15

    # Costanti Colore
    color_cyan = "#64ffda"
    color_accent = "#007bff"
    color_error = "#ff5252"
    color_success = "#00c853"

    df_bibbia = load_data('database_bibbia.csv')

    # --- ELEMENTI UI ---
    dd_camp = ft.Dropdown(
        label="CAMPIONATO",
        options=[ft.dropdown.Option(c) for c in sorted(df_bibbia.index.tolist())] if df_bibbia is not None else [],
        text_size=14, height=60, border_color=color_accent
    )

    in_casa = ft.TextField(label="GOL CASA", value="0", expand=1, keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.CENTER)
    in_ospite = ft.TextField(label="GOL OSPITE", value="0", expand=1, keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.CENTER)
    in_punta = ft.TextField(label="QUOTA PUNTA", expand=1, keyboard_type=ft.KeyboardType.NUMBER, color=color_accent, border_color=color_accent)
    in_banca = ft.TextField(label="QUOTA BANCA", expand=1, keyboard_type=ft.KeyboardType.NUMBER, color=color_error, border_color=color_error)
    
    in_bank = ft.TextField(label="BANK €", value="100", expand=1, keyboard_type=ft.KeyboardType.NUMBER)
    in_stake_perc = ft.TextField(label="STAKE %", value="5", expand=1, keyboard_type=ft.KeyboardType.NUMBER)
    in_comm = ft.TextField(label="COMM %", value="4.5", expand=1, keyboard_type=ft.KeyboardType.NUMBER)

    col_res = ft.Column(spacing=10)

    def analizza_click(e):
        col_res.controls.clear()
        
        if not dd_camp.value or not in_punta.value or not in_banca.value:
            page.snack_bar = ft.SnackBar(ft.Text("Mancano dati obbligatori!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            v_p = float(in_punta.value.replace(",", "."))
            v_b = float(in_banca.value.replace(",", "."))
            bank = float(in_bank.value.replace(",", "."))
            s_perc = float(in_stake_perc.value.replace(",", "."))
            comm = float(in_comm.value.replace(",", ".")) / 100
            c_score = f"{in_casa.value}-{in_ospite.value}"
            c_p, c_b = f"PUNTA_{c_score}", f"BANCA_{c_score}"
            
            if dd_camp.value in df_bibbia.index and c_p in df_bibbia.columns:
                lim_p = df_bibbia.loc[dd_camp.value, c_p]
                lim_b = df_bibbia.loc[dd_camp.value, c_b]

                ok_punta = v_p < lim_p
                ok_banca = v_b > lim_b
                trade_on = ok_punta and ok_banca
                
                rischio_max = bank * (s_perc / 100)
                prof_punta = (rischio_max * (v_p - 1)) * (1 - comm)
                puntata_lay = rischio_max / (v_b - 1)
                prof_banca = puntata_lay * (1 - comm)

                # 1. Target Card
                mercato = f"OVER {int(in_casa.value) + int(in_ospite.value) + 0.5}"
                col_res.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"TARGET: {mercato}", weight="bold", color=color_cyan),
                            ft.Row([
                                ft.Icon(ft.Icons.VERIFIED if ok_punta else ft.Icons.CANCEL, color="green" if ok_punta else "red", size=16),
                                ft.Text("PUNTA", size=12),
                                ft.Icon(ft.Icons.VERIFIED if ok_banca else ft.Icons.CANCEL, color="green" if ok_banca else "red", size=16),
                                ft.Text("BANCA", size=12),
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10, bgcolor="#1a1a2e", border_radius=8
                    )
                )

                if trade_on:
                    if prof_punta >= prof_banca:
                        consiglio, p_netto = "PUNTARE", prof_punta
                        dettaglio = f"Stake: € {rischio_max:.2f}"
                    else:
                        consiglio, p_netto = "BANCARE", prof_banca
                        dettaglio = f"Puntata Lay: € {puntata_lay:.2f}\n(Rischio: € {rischio_max:.2f})"

                    col_res.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text("✅ TRADE ON", size=22, weight="black", color=color_success),
                                ft.Text(f"{consiglio} (QUOTA MIGLIORE)", size=16, weight="bold"),
                                ft.Text(dettaglio, text_align=ft.TextAlign.CENTER),
                                ft.Text(f"NETTO: € {p_netto:.2f}", size=18, weight="bold", color=color_success)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                            padding=15, bgcolor="#16213e", border_radius=12, border=ft.border.all(2, color_success)
                        )
                    )
                else:
                    col_res.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text("❌ RISK OFF", size=22, weight="black", color=color_error),
                                ft.Text("Filtri non soddisfatti", size=14, italic=True)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=15, bgcolor="#16213e", border_radius=12
                        )
                    )
            else:
                col_res.controls.append(ft.Text("⚠️ Campionato o Risultato non in DB", color="orange"))
        except Exception as ex:
            col_res.controls.append(ft.Text(f"Errore: {str(ex)}", color="red"))
        page.update()

    btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.RADAR), ft.Text("ANALIZZA MATCH", weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
        on_click=analizza_click, height=55, style=ft.ButtonStyle(bgcolor=color_accent, color="white", shape=ft.RoundedRectangleBorder(radius=10))
    )

    page.add(
        ft.Column([
            ft.Row([ft.Icon(ft.Icons.ANALYTICS, color=color_cyan), ft.Text("TYPO HT-PRO MOBILE", size=20, weight="black")], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(height=5, color="#2e3b4e"),
            dd_camp,
            ft.Row([in_casa, in_ospite]),
            ft.Row([in_punta, in_banca]),
            ft.Row([in_bank, in_stake_perc, in_comm]),
            ft.Container(btn, padding=ft.padding.only(top=10, bottom=10)),
            col_res
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)
