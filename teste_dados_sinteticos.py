"""Testes do dados_sinteticos.py."""
import pandas as pd

import dados_sinteticos as ds
from recomendador import CAMPOS_PERFIL, validar_perfil

df = ds.gerar_perfis()

# 1) formato
assert list(df.columns) == CAMPOS_PERFIL + ["aprovado"]
assert len(df) == ds.N_PERFIS == 10000
assert set(df["aprovado"].unique()) == {0, 1}
print("1) formato OK:", df.shape)

# 2) reprodutivel: mesma semente = mesma tabela; outra semente = tabela diferente
pd.testing.assert_frame_equal(df, ds.gerar_perfis(ds.N_PERFIS, ds.SEMENTE))
assert not df.equals(ds.gerar_perfis(ds.N_PERFIS, 7))
print("2) reprodutibilidade OK")

# 3) todos os perfis passam na validacao do contrato (secao 7)
for linha in df[CAMPOS_PERFIL].to_dict("records"):
    erros = validar_perfil(linha)
    assert erros == [], f"perfil invalido: {linha} -> {erros}"
print("3) os 10.000 perfis sao validos OK")

# 4) faixas e combinacoes (secao 9)
assert df["renda"].between(900, 40000).all()
assert df["tempo_vinculo"].between(1, 480).all()
assert (df["credito"] % 1000 == 0).all()
for objetivo, (minimo, maximo) in ds.FAIXA_CREDITO.items():
    sub = df[df["objetivo"] == objetivo]
    assert sub["credito"].between(minimo, maximo).all(), objetivo
    assert set(sub["prazo"]) <= set(ds.PRAZOS_POR_OBJETIVO[objetivo]), objetivo
assert (df["entrada"] < df["credito"]).all()
print("4) faixas e prazos por objetivo OK")

# 5) ruido: exatamente 5% dos rotulos diferem do rotulo base
diferentes = (df["aprovado"] != ds.rotulo_base(df).astype(int)).sum()
assert diferentes == 500, diferentes
print("5) ruido de exatamente 5% OK (500 rotulos invertidos)")

# 6) nota calculada a mao: servidor, renda 8000, credito 200000, entrada 40000...
exemplo = pd.DataFrame([{"renda": 8000.0, "vinculo": "Servidor público",
    "tempo_vinculo": 96, "dividas_mensais": 500.0, "restricao": False,
    "entrada": 40000.0, "objetivo": "Imóvel", "credito": 200000.0, "prazo": 180}])
assert round(float(ds.calcular_nota(exemplo).iloc[0]), 2) == 94.79
assert not ds.recusado_pela_politica(exemplo).iloc[0]
print("6) nota de exemplo OK (94,79)")

# 7) conferencias obrigatorias do contrato
c = ds.conferencias(df)
print("   recusados pela politica:", f"{c['recusados_pela_politica']:.1%}")
print("   aprovados no total:     ", f"{c['aprovados_no_total']:.1%}")
print("   perfis de fronteira:    ", f"{c['fronteira']:.1%}")
assert c["ok_politica"] and c["ok_aprovados"] and c["ok_fronteira"]
print("7) conferencias do contrato OK")

print("TUDO CERTO")