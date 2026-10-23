import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.sqlite")})
    return app.test_client()


def abrir(c, eq=1, op="João"):
    return c.post("/api/v1/paradas", json={"equipamento_id": eq, "operador": op})


def test_health(client):
    assert client.get("/api/v1/health").get_json() == {"status": "ok"}


def test_cinco_maquinas(client):
    nomes = [e["nome"] for e in client.get("/api/v1/equipamentos").get_json()]
    assert nomes == [f"Máquina {i:02d}" for i in range(1, 6)]


def test_motivos_carregados(client):
    assert len(client.get("/api/v1/motivos").get_json()) >= 10


def test_abrir_parada_com_operador_digitado(client):
    r = abrir(client, op="  Maria Silva ")
    assert r.status_code == 201
    assert r.get_json()["operador"] == "Maria Silva"
    assert r.get_json()["status"] == "ABERTA"


def test_operador_obrigatorio(client):
    assert abrir(client, op="").status_code == 400
    assert abrir(client, op="A").status_code == 400


def test_operador_reaproveitado(client):
    abrir(client, 1, "Carlos"); abrir(client, 2, "carlos")
    assert client.get("/api/v1/operadores").get_json() == ["Carlos"]


def test_equipamento_inexistente(client):
    assert abrir(client, eq=999).status_code == 404


def test_sem_parada_simultanea(client):
    abrir(client)
    assert abrir(client).status_code == 409


def test_fluxo_completo(client):
    pid = abrir(client).get_json()["id"]
    assert client.patch(f"/api/v1/paradas/{pid}", json={"motivo_id": 1}).status_code == 200
    p = client.post(f"/api/v1/paradas/{pid}/retomar").get_json()
    assert p["status"] == "FECHADA" and p["duracao_min"] >= 0


def test_retomar_sem_motivo_fica_aguardando(client):
    pid = abrir(client).get_json()["id"]
    assert client.post(f"/api/v1/paradas/{pid}/retomar").get_json()["status"] == "AGUARDANDO_MOTIVO"
    assert client.patch(f"/api/v1/paradas/{pid}", json={"motivo_id": 2}).get_json()["status"] == "FECHADA"


def test_motivo_invalido(client):
    pid = abrir(client).get_json()["id"]
    assert client.patch(f"/api/v1/paradas/{pid}", json={"motivo_id": 999}).status_code == 400


def test_retomar_duas_vezes(client):
    pid = abrir(client).get_json()["id"]
    client.post(f"/api/v1/paradas/{pid}/retomar")
    assert client.post(f"/api/v1/paradas/{pid}/retomar").status_code == 409


def test_pareto_e_resumo(client):
    pid = abrir(client).get_json()["id"]
    client.patch(f"/api/v1/paradas/{pid}", json={"motivo_id": 1})
    client.post(f"/api/v1/paradas/{pid}/retomar")
    assert client.get("/api/v1/analytics/pareto").get_json()[0]["pct_acumulado"] == 100.0
    assert client.get("/api/v1/analytics/resumo").get_json()["total_paradas"] == 1


def test_titulo_e_acessibilidade(client):
    html = client.get("/").get_data(as_text=True)
    assert "Paradas de Máquina" in html and 'lang="pt-BR"' in html and 'for="operador"' in html
    assert "img/logo.png" in html


def test_dashboard(client):
    assert client.get("/dashboard").status_code == 200
