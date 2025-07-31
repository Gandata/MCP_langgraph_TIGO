#!/usr/bin/env python3
"""
Script de lanzamiento para la aplicación Streamlit de B2Bot.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Lanza la aplicación Streamlit."""
    
    # Obtener la ruta del proyecto
    project_root = Path(__file__).parent
    streamlit_app = project_root / "streamlit_app.py"
    
    # Verificar que el archivo existe
    if not streamlit_app.exists():
        print(f"❌ Error: No se encontró {streamlit_app}")
        sys.exit(1)
    
    # Comando para ejecutar Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(streamlit_app),
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("Iniciando B2Bot Streamlit App...")
    print(f"Directorio del proyecto: {project_root}")
    print(f"La aplicación estará disponible en: http://localhost:8501")
    print("=" * 60)
    
    try:
        # Cambiar al directorio del proyecto
        os.chdir(project_root)
        
        # Ejecutar Streamlit
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\nAplicación detenida por el usuario.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar Streamlit: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
