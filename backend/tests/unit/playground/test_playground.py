from backend.playground.playground import Playground

def test_playground_init_default():
    playground = Playground("test_id")
    assert playground.playground_id == "test_id"
    assert playground.description is None
    assert playground.models == {}
    assert playground.chain == []
    assert playground.active_chain is False

def test_playground_init_with_values():
    models = {"model1": {"input": "text", "output": "text"}}
    chain = ["model1"]
    playground = Playground("test_id", "Test description", models, chain)
    assert playground.playground_id == "test_id"
    assert playground.description == "Test description"
    assert playground.models == models
    assert playground.chain == chain
    assert playground.active_chain is False

def test_playground_to_dict():
    models = {"model1": {"input": "text", "output": "text"}}
    chain = ["model1"]
    playground = Playground("test_id", "Test description", models, chain)
    playground_dict = playground.to_dict()
    assert playground_dict == {
        "description": "Test description",
        "models": models,
        "chain": chain,
        "active_chain": False
    }