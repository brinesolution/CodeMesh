class CodeMeshError(Exception):
    code = "CODEMESH_ERROR"


class OllamaUnavailable(CodeMeshError):
    code = "OLLAMA_UNAVAILABLE"


class ModelNotInstalled(CodeMeshError):
    code = "MODEL_NOT_INSTALLED"


class RouterFailure(CodeMeshError):
    code = "ROUTER_FAILURE"


class GenerationTimeout(CodeMeshError):
    code = "GENERATION_TIMEOUT"


class GenerationCancelled(CodeMeshError):
    code = "GENERATION_CANCELLED"


class PersistenceFailure(CodeMeshError):
    code = "PERSISTENCE_FAILURE"

