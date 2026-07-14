from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from argentina_economic_data.inflation import Artifact, PipelineError, extract_ipc, promote


class InflationTests(unittest.TestCase):
    def artifact(self, path: Path) -> Artifact:
        return Artifact("test", "https://example.test/source.csv", path, "a" * 64, 101, "2026-01-01T00:00:00Z")

    def write_ipc(self, path: Path, duplicate: bool = False) -> None:
        fields = ["Codigo", "Descripcion", "Clasificador", "Periodo", "Indice_IPC", "v_m_IPC", "v_i_a_IPC", "Region"]
        with path.open("w", encoding="latin-1", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
            writer.writeheader()
            for month in range(1, 14):
                year, mo = (2016, 12) if month == 1 else (2017, month - 1)
                period = f"{year}{mo:02d}"
                index = 100 * (1.01 ** (month - 1))
                for code in ["0", "Núcleo", "Regulados", "Estacional"]:
                    writer.writerow({"Codigo": code, "Descripcion": "", "Clasificador": "Categorias",
                                     "Periodo": period, "Indice_IPC": f"{index:.4f}".replace(".", ","),
                                     "v_m_IPC": "NA" if month == 1 else "1,0", "v_i_a_IPC": "NA",
                                     "Region": "Nacional"})
            if duplicate:
                writer.writerow({"Codigo": "0", "Descripcion": "", "Clasificador": "Categorias",
                                 "Periodo": "201612", "Indice_IPC": "100", "v_m_IPC": "NA",
                                 "v_i_a_IPC": "NA", "Region": "Nacional"})

    def test_extract_ipc_balanced_panel(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ipc.csv"
            self.write_ipc(path)
            rows = extract_ipc(self.artifact(path))
            self.assertEqual(len(rows), 4 * (13 + 12))
            self.assertEqual({r["period"] for r in rows}, {"2016-12"} | {f"2017-{m:02d}" for m in range(1, 13)})

    def test_duplicate_fails_visibly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ipc.csv"
            self.write_ipc(path, duplicate=True)
            with self.assertRaisesRegex(PipelineError, "duplicadas"):
                extract_ipc(self.artifact(path))

    def test_promotion_rejects_deletions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = {"series_id": "x", "frequency": "monthly", "value": "1.000000", "unit": "index",
                    "status": "official", "source_id": "s", "source_url": "u", "source_sha256": "h",
                    "retrieved_at": "t"}
            promote([base | {"period": "2020-01"}, base | {"period": "2020-02"}], root, "one")
            with self.assertRaisesRegex(PipelineError, "elimina"):
                promote([base | {"period": "2020-02"}], root, "two")


if __name__ == "__main__":
    unittest.main()
