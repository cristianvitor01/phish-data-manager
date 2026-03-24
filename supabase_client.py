import os
from typing import Optional

from supabase import create_client, Client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "As variáveis SUPABASE_URL e SUPABASE_ANON_KEY (ou SUPABASE_KEY) são obrigatórias."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABELA = "mensagens"
CAMPOS_PERMITIDOS = {
    "texto",
    "classificacao",
    "tipo_golpe",
    "fonte",
    "data_cadastro",
    "observacoes",
    "revisada",
}


def filtrar_dados(dados: dict) -> dict:
    if not isinstance(dados, dict):
        return {}
    return {k: v for k, v in dados.items() if k in CAMPOS_PERMITIDOS}


def listar_mensagens(filtros: Optional[dict] = None):
    try:
        query = supabase.table(TABELA).select("*").order("id", desc=True)

        filtros = filtros or {}

        if filtros.get("classificacao"):
            query = query.eq("classificacao", filtros["classificacao"])

        if filtros.get("tipo_golpe"):
            query = query.eq("tipo_golpe", filtros["tipo_golpe"])

        if filtros.get("fonte"):
            query = query.eq("fonte", filtros["fonte"])

        if "revisada" in filtros:
            query = query.eq("revisada", filtros["revisada"])

        if filtros.get("busca"):
            query = query.ilike("texto", f"%{filtros['busca']}%")

        response = query.execute()
        return response.data or []
    except Exception as e:
        raise RuntimeError(f"Erro ao listar mensagens no Supabase: {e}")


def criar_mensagem(dados: dict):
    try:
        payload = filtrar_dados(dados)
        response = supabase.table(TABELA).insert(payload).execute()
        return response.data or []
    except Exception as e:
        raise RuntimeError(f"Erro ao criar mensagem no Supabase: {e}")


def buscar_mensagem(mensagem_id: int):
    try:
        response = (
            supabase
            .table(TABELA)
            .select("*")
            .eq("id", mensagem_id)
            .maybe_single()
            .execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar mensagem no Supabase: {e}")


def atualizar_mensagem(mensagem_id: int, dados: dict):
    try:
        payload = filtrar_dados(dados)
        response = (
            supabase
            .table(TABELA)
            .update(payload)
            .eq("id", mensagem_id)
            .execute()
        )
        return response.data or []
    except Exception as e:
        raise RuntimeError(f"Erro ao atualizar mensagem no Supabase: {e}")


def deletar_mensagem(mensagem_id: int):
    try:
        response = (
            supabase
            .table(TABELA)
            .delete()
            .eq("id", mensagem_id)
            .execute()
        )
        return response.data or []
    except Exception as e:
        raise RuntimeError(f"Erro ao deletar mensagem no Supabase: {e}")


def stats_mensagens():
    try:
        registros = listar_mensagens()

        total = len(registros)
        fraudes = sum(1 for m in registros if m.get("classificacao") == "fraude")
        legitimas = sum(1 for m in registros if m.get("classificacao") == "legitima")
        suspeitas = sum(1 for m in registros if m.get("classificacao") == "suspeita")
        revisadas = sum(1 for m in registros if bool(m.get("revisada")))

        por_tipo = {}
        por_fonte = {}

        for m in registros:
            tipo = m.get("tipo_golpe")
            fonte = m.get("fonte")

            if tipo:
                por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

            if fonte:
                por_fonte[fonte] = por_fonte.get(fonte, 0) + 1

        return {
            "total": total,
            "fraudes": fraudes,
            "legitimas": legitimas,
            "suspeitas": suspeitas,
            "revisadas": revisadas,
            "por_tipo": por_tipo,
            "por_fonte": por_fonte,
        }
    except Exception as e:
        raise RuntimeError(f"Erro ao gerar estatísticas: {e}")