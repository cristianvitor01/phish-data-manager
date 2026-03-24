import os
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Retorna um cliente Supabase configurado com variáveis de ambiente."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        raise RuntimeError(
            'Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.'
        )

    return create_client(url, key)


# Exemplo de funções utilitárias para uso no app

def listar_mensagens():
    supabase = get_supabase_client()
    response = supabase.table('mensagens').select('*').order('id', desc=True).execute()
    if response.error:
        raise RuntimeError(f'Erro Supabase listar_mensagens: {response.error.message}')
    return response.data


def criar_mensagem(dados: dict):
    supabase = get_supabase_client()
    response = supabase.table('mensagens').insert(dados).execute()
    if response.error:
        raise RuntimeError(f'Erro Supabase criar_mensagem: {response.error.message}')
    return response.data


def buscar_mensagem(mensagem_id: int):
    supabase = get_supabase_client()
    response = supabase.table('mensagens').select('*').eq('id', mensagem_id).single().execute()
    if response.error:
        raise RuntimeError(f'Erro Supabase buscar_mensagem: {response.error.message}')
    return response.data


def atualizar_mensagem(mensagem_id: int, dados: dict):
    supabase = get_supabase_client()
    response = supabase.table('mensagens').update(dados).eq('id', mensagem_id).execute()
    if response.error:
        raise RuntimeError(f'Erro Supabase atualizar_mensagem: {response.error.message}')
    return response.data


def deletar_mensagem(mensagem_id: int):
    supabase = get_supabase_client()
    response = supabase.table('mensagens').delete().eq('id', mensagem_id).execute()
    if response.error:
        raise RuntimeError(f'Erro Supabase deletar_mensagem: {response.error.message}')
    return response.data


def stats_mensagens():
    registros = listar_mensagens()
    total = len(registros)
    fraudes = sum(1 for m in registros if m.get('classificacao') == 'fraude')
    legitimas = sum(1 for m in registros if m.get('classificacao') == 'legitima')
    suspeitas = sum(1 for m in registros if m.get('classificacao') == 'suspeita')
    revisadas = sum(1 for m in registros if bool(m.get('revisada')))

    por_tipo = {}
    por_fonte = {}
    for m in registros:
        t = m.get('tipo_golpe')
        f = m.get('fonte')
        if t:
            por_tipo[t] = por_tipo.get(t, 0) + 1
        if f:
            por_fonte[f] = por_fonte.get(f, 0) + 1

    return {
        'total': total,
        'fraudes': fraudes,
        'legitimas': legitimas,
        'suspeitas': suspeitas,
        'revisadas': revisadas,
        'por_tipo': por_tipo,
        'por_fonte': por_fonte,
    }

