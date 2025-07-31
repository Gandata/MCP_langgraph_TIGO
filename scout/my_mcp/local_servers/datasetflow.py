import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as stats
from mcp.server.fastmcp import FastMCP
from typing import Optional
import duckdb
import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

mcp = FastMCP("datasetflow")

class DatasetFlowSession:
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.working_dir = os.environ.get("MCP_FILESYSTEM_DIR", None)

    async def load_random_dataset(self) -> str:
        try:
            df = sns.load_dataset('mpg').dropna()
            n = min(1000, len(df))
            self.data = df.sample(n=n, random_state=42).reset_index(drop=True)
            desc = (
                f"Dataset 'mpg' (automóviles 1970-1982).\n"
                f"Filas: {len(self.data)}  |  Columnas: {len(self.data.columns)}\n\n"
                f"{self.data.dtypes.to_string()}\n\n"
                f"{self.data.describe(include='all').T[['count','mean','std','min','max']]}"
            )
            return desc
        except Exception as e:
            return f"Error loading dataset: {str(e)}"

    async def query_data(self, sql_query: str) -> str:
        """Ejecuta un query SQL sobre el dataset y devuelve head(10)."""
        if self.data is None:
            return "No data loaded."
        try:
            con = duckdb.connect(database=':memory:')
            con.register('data', self.data)
            result = con.execute(sql_query).fetchdf()
            return result.head(10).to_string()
        except Exception as e:
            return f"Error executing query: {str(e)}"

    async def visualize_variable(self, column: str) -> str:
        """Genera histograma, qq-plot y boxplot para la variable numérica dada."""
        if self.data is None:
            return "No data loaded."
        if column not in self.data.columns:
            return f"Column '{column}' not found."
        if not pd.api.types.is_numeric_dtype(self.data[column]):
            return f"Column '{column}' is not numeric."

        plt.style.use("seaborn-v0_8")
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))

        # Histogram
        sns.histplot(self.data[column], kde=True, ax=ax[0])
        ax[0].set_title(f"Histograma de {column}")

        # Q-Q plot
        stats.probplot(self.data[column], dist="norm", plot=ax[1])
        ax[1].set_title(f"Q-Q plot de {column}")

        # Boxplot
        sns.boxplot(x=self.data[column], ax=ax[2])
        ax[2].set_title(f"Boxplot de {column}")

        plt.tight_layout()
        file_path = os.path.join(self.working_dir or ".", f"{column}_plots.png")
        fig.savefig(file_path)
        plt.close(fig)
        return f"Gráficos guardados en {file_path}"

    async def visualize_correlation(self) -> str:
        """Genera y guarda un heatmap de correlación de variables numéricas."""
        if self.data is None:
            return "No data loaded."
        numeric = self.data.select_dtypes(include='number')
        if numeric.empty:
            return "No numeric columns to correlate."

        plt.figure(figsize=(8, 6))
        sns.heatmap(numeric.corr(), annot=True, fmt=".2f", cmap="coolwarm")
        file_path = os.path.join(self.working_dir or ".", "correlation.png")
        plt.title("Matriz de correlación")
        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()
        return f"Heatmap guardado en {file_path}"

    async def normality_test(self) -> str:
        """Aplica test de normalidad (Shapiro-Wilk) a variables numéricas y devuelve tabla."""
        if self.data is None:
            return "No data loaded."
        numeric = self.data.select_dtypes(include='number')
        if numeric.empty:
            return "No numeric columns to test."

        results = []
        for col in numeric.columns:
            stat, p = stats.shapiro(numeric[col])
            results.append({
                "variable": col,
                "stat": round(stat, 4),
                "p_value": round(p, 4),
                "normal": "Sí" if p > 0.05 else "No"
            })
        return pd.DataFrame(results).to_string(index=False)

# Instancia global
session = DatasetFlowSession()

@mcp.tool()
async def load_random_dataset() -> str:
    """Carga 1000 filas aleatorias del dataset 'mpg' y devuelve descripción."""
    return await session.load_random_dataset()

@mcp.tool()
async def query_data(sql_query: str) -> str:
    """Ejecuta una consulta SQL sobre el dataset cargado."""
    return await session.query_data(sql_query)

@mcp.tool()
async def visualize_variable(column: str) -> str:
    """Visualiza histograma, qq-plot y boxplot de la columna numérica."""
    return await session.visualize_variable(column)

@mcp.tool()
async def visualize_correlation() -> str:
    """Genera y guarda heatmap de correlaciones."""
    return await session.visualize_correlation()

@mcp.tool()
async def normality_test() -> str:
    """Aplica test de normalidad Shapiro-Wilk a todas las variables numéricas."""
    return await session.normality_test()

if __name__ == "__main__":
    mcp.run(transport='stdio')