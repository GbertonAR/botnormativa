import sqlite3
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def finalizar_analisis(nombre_db="./docu/normativas.db"):
    """Finaliza o processamento dos dados e atualiza o campo 'etapa' na tabela 'normativas'."""
    try:
        conn = sqlite3.connect(nombre_db)
        cursor = conn.cursor()

        # Ler IDs de normativas com artigos processados
        cursor.execute("SELECT DISTINCT normativa_id FROM articulos")
        normativa_ids = cursor.fetchall()

        for normativa_id, in normativa_ids:
            # Realizar análise adicional (exemplo: contar palavras)
            cursor.execute("SELECT contenido FROM articulos WHERE normativa_id = ?", (normativa_id,))
            articulos = cursor.fetchall()
            total_palabras = 0
            for articulo, in articulos:
                total_palabras += len(articulo.split())
            logging.info(f"Normativa {normativa_id}: Total de palavras nos artigos = {total_palabras}")

            # Atualizar o campo 'etapa' na tabela 'normativas'
            cursor.execute("UPDATE normativas SET etapa = 'finalizado' WHERE id = ?", (normativa_id,))
            logging.info(f"Normativa {normativa_id} finalizada.")

        conn.commit()
        conn.close()
        logging.info("Processo de finalização concluído.")

    except sqlite3.Error as e:
        logging.error(f"Erro ao finalizar análise: {e}")

if __name__ == "__main__":
    finalizar_analisis()