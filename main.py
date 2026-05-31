"""
HubSpot Contact Sync
====================
Sync contacts from Google Sheets (or CSV) into HubSpot with
deduplication, field mapping, and upsert logic.

Usage:
    python main.py --csv data/sample_contacts.csv
    python main.py --sheet <GOOGLE_SHEET_ID>
    python main.py --csv data/sample_contacts.csv --dry-run
    python main.py --csv data/sample_contacts.csv --mode create_only
"""
import argparse
import os
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track
from rich.table import Table

from sync import read_sheet, HubSpotClient

load_dotenv()
console = Console()


def print_results(results: list[dict], dry_run: bool):
    created  = [r for r in results if "create" in r["action"]]
    updated  = [r for r in results if "update" in r["action"]]
    skipped  = [r for r in results if r["action"] == "skipped"]
    errors   = [r for r in results if r["action"] == "error"]

    mode_tag = "[dim](DRY RUN)[/dim] " if dry_run else ""

    console.print(f"\n{mode_tag}[bold green]Sync complete[/bold green]")
    console.print(f"  ✅ Created : [cyan]{len(created)}[/cyan]")
    console.print(f"  🔄 Updated : [cyan]{len(updated)}[/cyan]")
    console.print(f"  ⏭  Skipped : [dim]{len(skipped)}[/dim]")
    console.print(f"  ❌ Errors  : [red]{len(errors)}[/red]")

    if errors:
        table = Table(title="Errors", style="red")
        table.add_column("Email")
        table.add_column("Reason")
        for e in errors:
            table.add_row(e["email"], e["reason"])
        console.print(table)

    # Save results log
    out_path = f"data/sync_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    pd.DataFrame(results).to_csv(out_path, index=False)
    console.print(f"\n[dim]Log saved → {out_path}[/dim]\n")


def main():
    parser = argparse.ArgumentParser(description="Sync Google Sheets contacts to HubSpot")
    parser.add_argument("--csv",     help="Path to local CSV file")
    parser.add_argument("--sheet",   help="Google Sheet ID (overrides .env)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to HubSpot")
    parser.add_argument("--mode",    choices=["upsert", "create_only", "update_only"], default="upsert")
    args = parser.parse_args()

    if not args.csv and not args.sheet:
        console.print("[red]Error:[/red] Provide --csv <path> or --sheet <id>")
        sys.exit(1)

    dry_run = args.dry_run or os.getenv("DRY_RUN", "false").lower() == "true"

    # Load data
    console.print(f"\n[bold yellow]HubSpot Contact Sync[/bold yellow]")
    if dry_run:
        console.print("[dim]Mode: DRY RUN — no changes will be made[/dim]\n")

    try:
        df = read_sheet(sheet_id=args.sheet, csv_path=args.csv)
    except Exception as e:
        console.print(f"[red]Failed to load data: {e}[/red]")
        sys.exit(1)

    console.print(f"Loaded [cyan]{len(df)}[/cyan] contacts from source\n")

    # Init HubSpot client
    try:
        client = HubSpotClient()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        console.print("Add HUBSPOT_API_KEY to your .env file")
        sys.exit(1)

    # Run sync
    rows = df.to_dict(orient="records")
    results = client.batch_upsert(rows, dry_run=dry_run)

    print_results(results, dry_run)


if __name__ == "__main__":
    main()
