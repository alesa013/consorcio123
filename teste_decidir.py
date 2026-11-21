# teste_decidir.py - confere a decidir() com 4 perfis de referência
import recomendador

BASE = {
    "renda": 4500.0, "vinculo": "CLT", "tempo_vinculo": 36,
    "dividas_mensais": 500.0, "restricao": False, "entrada": 20000.0,
    "objetivo": "Imóvel", "credito": 120000.0, "prazo": 120,
}

casos = {
    "1. Perfil comum (deve passar pelo modelo)": dict(BASE),
    "2. Com restrição no nome": {**BASE, "restricao": True},
    "3. Renda baixa": {**BASE, "renda": 1200.0, "dividas_mensais": 0.0,
                       "credito": 20000.0, "entrada": 4000.0, "prazo": 60},
    "4. Comprometimento alto": {**BASE, "credito": 400000.0, "entrada": 0.0,
                                "prazo": 36},
}

for nome, perfil in casos.items():
    erros = recomendador.validar_perfil(perfil)
    print("\n" + nome)
    if erros:
        print("  Perfil inválido:", erros)
        continue
    d = recomendador.decidir(perfil)
    print("  status:", d["status"], "| prob.:", round(d["probabilidade"], 3),
          "| origem:", d["origem"])
    print("  motivo:", d["motivo"])
    print("  fatores:", d["fatores"])