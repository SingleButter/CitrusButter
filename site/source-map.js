window.CITRUS_SOURCE_FILES = [
  {
    "group": "package",
    "path": "src/citrus/__init__.py",
    "description": "包入口，暴露项目版本号。",
    "symbols": [
      "__version__"
    ],
    "content": "\"\"\"CitrusButter public package.\"\"\"\n\n__version__ = \"0.1.0\"\n\n"
  },
  {
    "group": "cli",
    "path": "src/citrus/cli/__init__.py",
    "description": "CLI 子包入口，保持轻量导出。",
    "symbols": [],
    "content": "\"\"\"Command-line interface package for CitrusButter.\"\"\"\n\n"
  },
  {
    "group": "cli",
    "path": "src/citrus/cli/app.py",
    "description": "Typer 命令入口，负责解析参数、读取配置、创建 provider、接入权限审批并调用 runtime。",
    "symbols": [
      "_approve_permission",
      "run",
      "providers",
      "config"
    ],
    "content": "import json\nimport os\nfrom typing import Annotated\n\nimport typer\n\nfrom citrus.config.settings import ProviderSettingsError, build_provider, load_config\nfrom citrus.context.builder import ContextBuilder\nfrom citrus.permissions.base import PermissionDecision, PermissionRequest\nfrom citrus.permissions.policy import GradedPermissionPolicy\nfrom citrus.providers.base import ModelResponse\nfrom citrus.providers.fake import FakeProvider\nfrom citrus.runtime.agent import AgentRuntime, RunRequest\nfrom citrus.runtime.messages import Message\nfrom citrus.sessions.memory import InMemorySessionStore\nfrom citrus.tools.registry import ToolRegistry\n\napp = typer.Typer(\n    help=\"CitrusButter: a modular coding agent harness.\",\n    no_args_is_help=True,\n)\n\n\ndef _approve_permission(request: PermissionRequest) -> PermissionDecision:\n    typer.echo(f\"Tool {request.tool_name} requires approval.\")\n    typer.echo(f\"Reason: {request.reason}\")\n    if request.command:\n        typer.echo(f\"Command: {request.command}\")\n    else:\n        arguments = json.dumps(\n            request.arguments,\n            ensure_ascii=False,\n            sort_keys=True,\n        )\n        typer.echo(f\"Arguments: {arguments}\")\n\n    approved = typer.confirm(f\"Allow tool {request.tool_name}?\", default=False)\n    if approved:\n        return PermissionDecision(outcome=\"allow\", reason=\"Approved by user.\")\n    return PermissionDecision(outcome=\"deny\", reason=\"Denied by user.\")\n\n\n@app.command()\ndef run(\n    task: Annotated[\n        str,\n        typer.Argument(help=\"Coding task for the CitrusButter runtime.\"),\n    ],\n    provider: Annotated[\n        str | None,\n        typer.Option(help=\"Provider to use. Defaults to config file.\"),\n    ] = None,\n    model: Annotated[\n        str | None,\n        typer.Option(help=\"Model override for real providers.\"),\n    ] = None,\n    fake_response: Annotated[\n        str,\n        typer.Option(help=\"Scripted response for the fake provider.\"),\n    ] = \"CitrusButter fake provider completed the task.\",\n) -> None:\n    \"\"\"Run a coding-agent task.\"\"\"\n    try:\n        config = load_config(os.environ)\n        selected_provider_name = provider or config.provider\n        selected_provider = (\n            FakeProvider(\n                responses=[\n                    ModelResponse(messages=[Message.assistant_text(fake_response)]),\n                ]\n            )\n            if selected_provider_name == \"fake\"\n            else build_provider(\n                selected_provider_name,\n                model=model,\n                env=os.environ,\n                config=config,\n            )\n        )\n    except ProviderSettingsError as exc:\n        typer.echo(str(exc), err=True)\n        raise typer.Exit(code=2) from exc\n\n    runtime = AgentRuntime(\n        provider=selected_provider,\n        tools=ToolRegistry.with_default_local_tools(),\n        permissions=GradedPermissionPolicy(auto_approve=False),\n        permission_approver=_approve_permission,\n        context=ContextBuilder(),\n        session_store=InMemorySessionStore(),\n    )\n    result = runtime.run(RunRequest(task=task))\n    typer.echo(result.final_message)\n\n\n@app.command()\ndef providers() -> None:\n    \"\"\"Show configured model providers.\"\"\"\n    typer.echo(\"anthropic\")\n    typer.echo(\"openai\")\n    typer.echo(\"deepseek\")\n    typer.echo(\"fake\")\n\n\n@app.command()\ndef config() -> None:\n    \"\"\"Show or update CitrusButter configuration.\"\"\"\n    loaded = load_config(os.environ)\n    typer.echo(f\"config={loaded.path}\")\n    typer.echo(f\"provider={os.getenv('CITRUS_PROVIDER', loaded.provider)}\")\n    typer.echo(f\"model={os.getenv('CITRUS_MODEL', loaded.model or '')}\")\n    for name, provider_config in sorted(loaded.providers.items()):\n        key_state = \"configured\" if provider_config.api_key else \"missing\"\n        model_state = provider_config.model or \"\"\n        typer.echo(f\"{name} api_key={key_state} model={model_state}\")\n    typer.echo(\"Environment variables override config file values.\")\n"
  },
  {
    "group": "config",
    "path": "src/citrus/config/__init__.py",
    "description": "配置模块入口，集中导出 provider 配置解析 API。",
    "symbols": [],
    "content": "\"\"\"Configuration helpers for CitrusButter.\"\"\"\n\n"
  },
  {
    "group": "config",
    "path": "src/citrus/config/settings.py",
    "description": "配置文件与环境变量解析层，统一产出可用于构建 provider 的设置。",
    "symbols": [
      "ProviderSettingsError",
      "ProviderConfig",
      "CitrusConfig",
      "ResolvedProviderSettings",
      "load_config",
      "resolve_provider_settings",
      "build_provider",
      "_config_path",
      "_provider_api_key",
      "_api_key_env_name",
      "_default_model",
      "_required_key"
    ],
    "content": "import tomllib\nfrom collections.abc import Mapping\nfrom pathlib import Path\n\nfrom pydantic import BaseModel, Field\n\nfrom citrus.providers.anthropic import AnthropicProvider\nfrom citrus.providers.base import ModelProvider\nfrom citrus.providers.deepseek import DeepSeekProvider\nfrom citrus.providers.openai import OpenAIProvider\n\n\nclass ProviderSettingsError(ValueError):\n    pass\n\n\nclass ProviderConfig(BaseModel):\n    api_key: str | None = None\n    model: str | None = None\n    base_url: str | None = None\n\n\nclass CitrusConfig(BaseModel):\n    path: Path | None = None\n    provider: str = \"fake\"\n    model: str | None = None\n    providers: dict[str, ProviderConfig] = Field(default_factory=dict)\n\n\nclass ResolvedProviderSettings(BaseModel):\n    provider: str\n    model: str | None\n    api_key: str | None\n    base_url: str | None = None\n\n\ndef load_config(env: Mapping[str, str], cwd: Path | None = None) -> CitrusConfig:\n    path = _config_path(env, cwd or Path.cwd())\n    if not path.exists():\n        return CitrusConfig(path=path)\n\n    with path.open(\"rb\") as file:\n        data = tomllib.load(file)\n\n    providers = {\n        name: ProviderConfig.model_validate(config)\n        for name, config in data.get(\"providers\", {}).items()\n    }\n    return CitrusConfig(\n        path=path,\n        provider=data.get(\"provider\", \"fake\"),\n        model=data.get(\"model\"),\n        providers=providers,\n    )\n\n\ndef resolve_provider_settings(\n    provider: str | None,\n    model: str | None,\n    config: CitrusConfig,\n    env: Mapping[str, str],\n) -> ResolvedProviderSettings:\n    selected_provider = (\n        provider or env.get(\"CITRUS_PROVIDER\") or config.provider\n    ).lower()\n    provider_config = config.providers.get(selected_provider, ProviderConfig())\n    selected_model = (\n        model\n        or env.get(\"CITRUS_MODEL\")\n        or provider_config.model\n        or config.model\n        or _default_model(selected_provider)\n    )\n    api_key = _provider_api_key(selected_provider, provider_config, env)\n    return ResolvedProviderSettings(\n        provider=selected_provider,\n        model=selected_model,\n        api_key=api_key,\n        base_url=provider_config.base_url,\n    )\n\n\ndef build_provider(\n    provider: str,\n    model: str | None,\n    env: Mapping[str, str],\n    config: CitrusConfig | None = None,\n) -> ModelProvider:\n    resolved = resolve_provider_settings(\n        provider=provider,\n        model=model,\n        config=config or load_config(env),\n        env=env,\n    )\n    normalized = resolved.provider\n\n    if normalized == \"anthropic\":\n        return AnthropicProvider(\n            api_key=_required_key(resolved, \"ANTHROPIC_API_KEY\"),\n            model=resolved.model or \"claude-sonnet-4-5\",\n        )\n\n    if normalized == \"openai\":\n        return OpenAIProvider(\n            api_key=_required_key(resolved, \"OPENAI_API_KEY\"),\n            model=resolved.model or \"gpt-4.1\",\n            base_url=resolved.base_url,\n        )\n\n    if normalized == \"deepseek\":\n        return DeepSeekProvider(\n            api_key=_required_key(resolved, \"DEEPSEEK_API_KEY\"),\n            model=resolved.model or \"deepseek-chat\",\n            base_url=resolved.base_url,\n        )\n\n    raise ProviderSettingsError(f\"Unknown provider: {provider}\")\n\n\ndef _config_path(env: Mapping[str, str], cwd: Path) -> Path:\n    explicit = env.get(\"CITRUS_CONFIG\")\n    if explicit:\n        return Path(explicit).expanduser()\n    project_local = cwd / \".citrus\" / \"config.toml\"\n    if project_local.exists():\n        return project_local\n    return Path.home() / \".config\" / \"citrus\" / \"config.toml\"\n\n\ndef _provider_api_key(\n    provider: str,\n    provider_config: ProviderConfig,\n    env: Mapping[str, str],\n) -> str | None:\n    env_key = _api_key_env_name(provider)\n    if env_key and env.get(env_key):\n        return env[env_key]\n    return provider_config.api_key\n\n\ndef _api_key_env_name(provider: str) -> str | None:\n    return {\n        \"anthropic\": \"ANTHROPIC_API_KEY\",\n        \"openai\": \"OPENAI_API_KEY\",\n        \"deepseek\": \"DEEPSEEK_API_KEY\",\n    }.get(provider)\n\n\ndef _default_model(provider: str) -> str | None:\n    return {\n        \"anthropic\": \"claude-sonnet-4-5\",\n        \"openai\": \"gpt-4.1\",\n        \"deepseek\": \"deepseek-chat\",\n        \"fake\": None,\n    }.get(provider)\n\n\ndef _required_key(resolved: ResolvedProviderSettings, env_name: str) -> str:\n    if not resolved.api_key:\n        raise ProviderSettingsError(\n            f\"Missing API key for {resolved.provider}. Set {env_name} \"\n            \"or add api_key to the CitrusButter config file.\"\n        )\n    return resolved.api_key\n"
  },
  {
    "group": "context",
    "path": "src/citrus/context/__init__.py",
    "description": "Context 子包入口，导出上下文构建器。",
    "symbols": [],
    "content": "\"\"\"Context assembly components.\"\"\"\n\n"
  },
  {
    "group": "context",
    "path": "src/citrus/context/builder.py",
    "description": "把用户任务转换为统一 Message；未来 repo summary 和 memory retrieval 会从这里接入。",
    "symbols": [
      "ContextBuilder"
    ],
    "content": "from citrus.runtime.messages import Message\n\n\nclass ContextBuilder:\n    \"\"\"Build model messages for a runtime turn.\"\"\"\n\n    def build(self, task: str) -> list[Message]:\n        return [Message.user_text(task)]\n\n"
  },
  {
    "group": "memory",
    "path": "src/citrus/memory/__init__.py",
    "description": "Memory 子包入口，导出存储、候选记忆和服务边界。",
    "symbols": [],
    "content": "\"\"\"Memory extension points.\"\"\"\n\n"
  },
  {
    "group": "memory",
    "path": "src/citrus/memory/base.py",
    "description": "长期记忆的核心协议和数据模型，区别于 session 事件历史。",
    "symbols": [
      "MemoryItem",
      "MemoryCandidate",
      "MemoryStore",
      "MemoryPolicy"
    ],
    "content": "from typing import Protocol\n\nfrom pydantic import BaseModel, Field\n\nfrom citrus.runtime.events import SessionEvent\n\n\nclass MemoryItem(BaseModel):\n    scope: str\n    content: str\n    tags: list[str] = Field(default_factory=list)\n\n\nclass MemoryCandidate(BaseModel):\n    scope: str\n    content: str\n    source_event: str | None = None\n\n\nclass MemoryStore(Protocol):\n    def search(self, query: str) -> list[MemoryItem]:\n        ...\n\n    def put(self, item: MemoryItem) -> None:\n        ...\n\n\nclass MemoryPolicy(Protocol):\n    def propose_updates(self, events: list[SessionEvent]) -> list[MemoryCandidate]:\n        ...\n\n"
  },
  {
    "group": "memory",
    "path": "src/citrus/memory/noop.py",
    "description": "V1 默认空 memory store，用于保留接口而不引入复杂持久化。",
    "symbols": [
      "NoopMemoryStore"
    ],
    "content": "from citrus.memory.base import MemoryItem\n\n\nclass NoopMemoryStore:\n    \"\"\"Memory store implementation that intentionally persists nothing.\"\"\"\n\n    def search(self, query: str) -> list[MemoryItem]:\n        return []\n\n    def put(self, item: MemoryItem | str, content: str | None = None) -> None:\n        return None\n"
  },
  {
    "group": "memory",
    "path": "src/citrus/memory/service.py",
    "description": "MemoryService 门面，隔离 runtime 与具体 memory store 实现。",
    "symbols": [
      "MemoryService"
    ],
    "content": "from citrus.memory.base import MemoryCandidate, MemoryItem, MemoryStore\nfrom citrus.runtime.events import SessionEvent\n\n\nclass MemoryService:\n    def __init__(self, store: MemoryStore) -> None:\n        self._store = store\n\n    def retrieve_for_task(self, task: str) -> list[MemoryItem]:\n        return self._store.search(task)\n\n    def propose_updates(self, events: list[SessionEvent]) -> list[MemoryCandidate]:\n        return []\n\n"
  },
  {
    "group": "permissions",
    "path": "src/citrus/permissions/__init__.py",
    "description": "权限模块入口，导出决策模型、审批请求、审批回调和默认分级策略。",
    "symbols": [],
    "content": "\"\"\"Permission policy components.\"\"\"\n\nfrom citrus.permissions.base import (\n    PermissionApprover,\n    PermissionDecision,\n    PermissionRequest,\n)\nfrom citrus.permissions.policy import GradedPermissionPolicy\n\n__all__ = [\n    \"GradedPermissionPolicy\",\n    \"PermissionApprover\",\n    \"PermissionDecision\",\n    \"PermissionRequest\",\n]\n"
  },
  {
    "group": "permissions",
    "path": "src/citrus/permissions/base.py",
    "description": "工具执行前的权限决策模型，表达 allow、ask、deny，以及 runtime 调用的审批请求与回调。",
    "symbols": [
      "PermissionDecision",
      "PermissionRequest",
      "PermissionOutcome",
      "PermissionApprover"
    ],
    "content": "from collections.abc import Callable\nfrom typing import Literal\n\nfrom pydantic import BaseModel\n\nPermissionOutcome = Literal[\"allow\", \"deny\", \"ask\"]\n\n\nclass PermissionDecision(BaseModel):\n    outcome: PermissionOutcome\n    reason: str\n\n\nclass PermissionRequest(BaseModel):\n    tool_name: str\n    tool_call_id: str\n    arguments: dict[str, object]\n    reason: str\n    command: str | None = None\n\n\nPermissionApprover = Callable[[PermissionRequest], PermissionDecision]\n"
  },
  {
    "group": "permissions",
    "path": "src/citrus/permissions/policy.py",
    "description": "默认分级权限策略：读操作放行，写入和 shell 进入审批或拒绝路径。",
    "symbols": [
      "GradedPermissionPolicy"
    ],
    "content": "from citrus.permissions.base import PermissionDecision\n\n\nclass GradedPermissionPolicy:\n    \"\"\"Small default policy for local coding tools.\"\"\"\n\n    def __init__(self, auto_approve: bool = False) -> None:\n        self.auto_approve = auto_approve\n\n    def evaluate_tool(\n        self,\n        tool_name: str,\n        command: str | None = None,\n    ) -> PermissionDecision:\n        if tool_name == \"read_file\":\n            return PermissionDecision(\n                outcome=\"allow\",\n                reason=\"File reads are safe by default.\",\n            )\n\n        if tool_name == \"write_file\":\n            return PermissionDecision(\n                outcome=\"ask\",\n                reason=\"File writes modify the workspace.\",\n            )\n\n        if tool_name == \"run_shell\":\n            if command and self._is_dangerous_shell_command(command):\n                return PermissionDecision(\n                    outcome=\"deny\",\n                    reason=\"Dangerous shell command denied by default.\",\n                )\n            return PermissionDecision(\n                outcome=\"ask\",\n                reason=\"Shell commands require approval.\",\n            )\n\n        return PermissionDecision(\n            outcome=\"ask\",\n            reason=\"Unknown tools require approval.\",\n        )\n\n    def _is_dangerous_shell_command(self, command: str) -> bool:\n        normalized = command.strip().lower()\n        return \"rm -rf\" in normalized or normalized.startswith(\"sudo \")\n"
  },
  {
    "group": "providers",
    "path": "src/citrus/providers/__init__.py",
    "description": "Provider 子包入口，导出统一 provider 协议和各厂商 adapter。",
    "symbols": [],
    "content": "\"\"\"Model provider adapters.\"\"\"\n\n"
  },
  {
    "group": "providers",
    "path": "src/citrus/providers/base.py",
    "description": "模型接入端口，定义 ToolSpec、ModelRequest、ModelResponse 和 ModelProvider。",
    "symbols": [
      "ToolSpec",
      "ModelRequest",
      "ModelResponse",
      "ModelProvider"
    ],
    "content": "from typing import Protocol\n\nfrom pydantic import BaseModel, Field\n\nfrom citrus.runtime.messages import Message\n\n\nclass ToolSpec(BaseModel):\n    name: str\n    description: str\n    input_schema: dict[str, object]\n\n\nclass ModelRequest(BaseModel):\n    messages: list[Message]\n    tools: list[ToolSpec] = Field(default_factory=list)\n    model: str | None = None\n    metadata: dict[str, str] = Field(default_factory=dict)\n\n\nclass ModelResponse(BaseModel):\n    messages: list[Message]\n    metadata: dict[str, str] = Field(default_factory=dict)\n\n\nclass ModelProvider(Protocol):\n    name: str\n\n    def complete(self, request: ModelRequest) -> ModelResponse:\n        ...\n"
  },
  {
    "group": "providers",
    "path": "src/citrus/providers/openai.py",
    "description": "OpenAI adapter，把内部消息、工具规范、tool call 和带 tool_call_id 的 tool result 映射到 OpenAI chat completions。",
    "symbols": [
      "OpenAIProvider"
    ],
    "content": "import json\nfrom typing import Any\n\nfrom citrus.providers.base import ModelRequest, ModelResponse, ToolSpec\nfrom citrus.runtime.messages import Message, ToolCall\n\n\nclass OpenAIProvider:\n    name = \"openai\"\n\n    def __init__(\n        self,\n        api_key: str,\n        model: str,\n        base_url: str | None = None,\n        client: Any | None = None,\n    ) -> None:\n        self.api_key = api_key\n        self.model = model\n        self.base_url = base_url\n        self._client = client\n\n    def complete(self, request: ModelRequest) -> ModelResponse:\n        client = self._client or self._build_client()\n        kwargs: dict[str, object] = {\n            \"model\": self.model,\n            \"messages\": [\n                self._message_to_openai(message) for message in request.messages\n            ],\n        }\n        if request.tools:\n            kwargs[\"tools\"] = [self._tool_to_openai(tool) for tool in request.tools]\n\n        response = client.chat.completions.create(**kwargs)\n        message = response.choices[0].message\n        tool_calls = getattr(message, \"tool_calls\", None) or []\n        if tool_calls:\n            return ModelResponse(\n                messages=[\n                    Message.assistant_tool_call(\n                        ToolCall(\n                            id=tool_call.id,\n                            name=tool_call.function.name,\n                            arguments=json.loads(tool_call.function.arguments),\n                        )\n                    )\n                    for tool_call in tool_calls\n                ]\n            )\n        return ModelResponse(messages=[Message.assistant_text(message.content or \"\")])\n\n    def _tool_to_openai(self, tool: ToolSpec) -> dict[str, object]:\n        return {\n            \"type\": \"function\",\n            \"function\": {\n                \"name\": tool.name,\n                \"description\": tool.description,\n                \"parameters\": tool.input_schema,\n            },\n        }\n\n    def _message_to_openai(self, message: Message) -> dict[str, object]:\n        if message.role == \"tool\":\n            if not message.tool_call_id:\n                raise ValueError(\"Tool messages require a tool_call_id.\")\n            return {\n                \"role\": \"tool\",\n                \"tool_call_id\": message.tool_call_id,\n                \"content\": message.text(),\n            }\n\n        tool_calls = message.tool_calls()\n        if tool_calls:\n            return {\n                \"role\": message.role,\n                \"content\": None,\n                \"tool_calls\": [\n                    {\n                        \"id\": tool_call.id,\n                        \"type\": \"function\",\n                        \"function\": {\n                            \"name\": tool_call.name,\n                            \"arguments\": json.dumps(tool_call.arguments),\n                        },\n                    }\n                    for tool_call in tool_calls\n                ],\n            }\n\n        return {\"role\": message.role, \"content\": message.text()}\n\n    def _build_client(self) -> Any:\n        from openai import OpenAI\n\n        if self.base_url:\n            return OpenAI(api_key=self.api_key, base_url=self.base_url)\n        return OpenAI(api_key=self.api_key)\n"
  },
  {
    "group": "providers",
    "path": "src/citrus/providers/deepseek.py",
    "description": "DeepSeek adapter，复用 OpenAI-compatible provider 并设置 DeepSeek base URL。",
    "symbols": [
      "DeepSeekProvider"
    ],
    "content": "from citrus.providers.openai import OpenAIProvider\n\n\nclass DeepSeekProvider(OpenAIProvider):\n    name = \"deepseek\"\n\n    def __init__(\n        self,\n        api_key: str,\n        model: str,\n        base_url: str | None = None,\n        client: object | None = None,\n    ) -> None:\n        super().__init__(\n            api_key=api_key,\n            model=model,\n            base_url=base_url or \"https://api.deepseek.com\",\n            client=client,\n        )\n"
  },
  {
    "group": "providers",
    "path": "src/citrus/providers/anthropic.py",
    "description": "Anthropic adapter，把内部消息、tool call 和 tool result 转换到 Anthropic messages API。",
    "symbols": [
      "AnthropicProvider"
    ],
    "content": "from typing import Any\n\nfrom citrus.providers.base import ModelRequest, ModelResponse, ToolSpec\nfrom citrus.runtime.messages import Message, TextBlock, ToolCall\n\n\nclass AnthropicProvider:\n    name = \"anthropic\"\n\n    def __init__(self, api_key: str, model: str, client: Any | None = None) -> None:\n        self.api_key = api_key\n        self.model = model\n        self._client = client\n\n    def complete(self, request: ModelRequest) -> ModelResponse:\n        client = self._client or self._build_client()\n        kwargs: dict[str, object] = {\n            \"model\": self.model,\n            \"max_tokens\": 4096,\n            \"messages\": [\n                {\n                    \"role\": message.role,\n                    \"content\": [\n                        {\"type\": \"text\", \"text\": block.text}\n                        for block in message.content\n                        if isinstance(block, TextBlock)\n                    ],\n                }\n                for message in request.messages\n                if message.role in {\"user\", \"assistant\"}\n            ],\n        }\n        if request.tools:\n            kwargs[\"tools\"] = [self._tool_to_anthropic(tool) for tool in request.tools]\n\n        response = client.messages.create(**kwargs)\n        messages: list[Message] = []\n        for block in response.content:\n            if getattr(block, \"type\", \"text\") == \"tool_use\":\n                messages.append(\n                    Message.assistant_tool_call(\n                        ToolCall(\n                            id=block.id,\n                            name=block.name,\n                            arguments=block.input,\n                        )\n                    )\n                )\n            else:\n                messages.append(Message.assistant_text(block.text))\n        return ModelResponse(messages=messages)\n\n    def _tool_to_anthropic(self, tool: ToolSpec) -> dict[str, object]:\n        return {\n            \"name\": tool.name,\n            \"description\": tool.description,\n            \"input_schema\": tool.input_schema,\n        }\n\n    def _build_client(self) -> Any:\n        from anthropic import Anthropic\n\n        return Anthropic(api_key=self.api_key)\n"
  },
  {
    "group": "providers",
    "path": "src/citrus/providers/fake.py",
    "description": "测试与 demo provider，用预设响应驱动 runtime 和 CLI 的可重复验证。",
    "symbols": [
      "FakeProvider"
    ],
    "content": "from collections.abc import Sequence\n\nfrom citrus.providers.base import ModelRequest, ModelResponse\n\n\nclass FakeProvider:\n    \"\"\"Deterministic provider for tests and offline demos.\"\"\"\n\n    name = \"fake\"\n\n    def __init__(self, responses: Sequence[ModelResponse]) -> None:\n        self._responses = list(responses)\n        self._index = 0\n        self.requests: list[ModelRequest] = []\n\n    def complete(self, request: ModelRequest) -> ModelResponse:\n        self.requests.append(request)\n        if self._index >= len(self._responses):\n            raise RuntimeError(\"FakeProvider has no scripted responses left.\")\n\n        response = self._responses[self._index]\n        self._index += 1\n        return response\n"
  },
  {
    "group": "runtime",
    "path": "src/citrus/runtime/__init__.py",
    "description": "Runtime 子包入口，导出 agent、事件和内部消息模型。",
    "symbols": [],
    "content": "\"\"\"Runtime kernel components.\"\"\"\n\n"
  },
  {
    "group": "runtime",
    "path": "src/citrus/runtime/agent.py",
    "description": "核心 agent loop：组装 context、调用 provider、处理工具调用、解析权限审批、记录事件并返回结果。",
    "symbols": [
      "RunRequest",
      "RunResult",
      "AgentRuntime"
    ],
    "content": "from pathlib import Path\nfrom uuid import uuid4\n\nfrom pydantic import BaseModel, Field\n\nfrom citrus.context.builder import ContextBuilder\nfrom citrus.memory.service import MemoryService\nfrom citrus.permissions.base import (\n    PermissionApprover,\n    PermissionDecision,\n    PermissionRequest,\n)\nfrom citrus.permissions.policy import GradedPermissionPolicy\nfrom citrus.providers.base import ModelProvider, ModelRequest, ToolSpec\nfrom citrus.runtime.events import EventType, RuntimeObserver, SessionEvent\nfrom citrus.runtime.messages import Message, ToolCall, ToolResult\nfrom citrus.sessions.base import SessionStore\nfrom citrus.tools.base import ToolContext\nfrom citrus.tools.registry import ToolRegistry\n\n\nclass RunRequest(BaseModel):\n    task: str\n    workspace: Path = Field(default_factory=Path.cwd)\n    session_id: str | None = None\n    max_turns: int = 8\n\n\nclass RunResult(BaseModel):\n    session_id: str\n    success: bool\n    final_message: str\n\n\nclass AgentRuntime:\n    def __init__(\n        self,\n        provider: ModelProvider,\n        tools: ToolRegistry,\n        permissions: GradedPermissionPolicy,\n        context: ContextBuilder,\n        session_store: SessionStore,\n        permission_approver: PermissionApprover | None = None,\n        memory: MemoryService | None = None,\n        observers: list[RuntimeObserver] | None = None,\n    ) -> None:\n        self._provider = provider\n        self._tools = tools\n        self._permissions = permissions\n        self._permission_approver = permission_approver\n        self._context = context\n        self._session_store = session_store\n        self._memory = memory\n        self._observers = observers or []\n\n    def run(self, request: RunRequest) -> RunResult:\n        session_id = request.session_id or str(uuid4())\n        workspace = request.workspace.resolve()\n\n        self._emit(session_id, EventType.TASK_STARTED, {\"task\": request.task})\n        messages = self._context.build(task=request.task)\n        self._emit(session_id, EventType.CONTEXT_BUILT, {\"messages\": len(messages)})\n\n        for _turn in range(request.max_turns):\n            self._emit(session_id, EventType.MODEL_REQUESTED, {})\n            response = self._provider.complete(\n                ModelRequest(messages=messages, tools=self._tool_specs())\n            )\n            self._emit(\n                session_id,\n                EventType.MODEL_RESPONDED,\n                {\"messages\": len(response.messages)},\n            )\n            messages.extend(response.messages)\n\n            tool_calls = self._collect_tool_calls(response.messages)\n            if not tool_calls:\n                final_message = self._final_text(response.messages)\n                self._emit(\n                    session_id,\n                    EventType.TASK_COMPLETED,\n                    {\"final_message\": final_message},\n                )\n                return RunResult(\n                    session_id=session_id,\n                    success=True,\n                    final_message=final_message,\n                )\n\n            for tool_call in tool_calls:\n                tool_result = self._execute_tool_call(session_id, tool_call, workspace)\n                if tool_result.is_error:\n                    final_message = tool_result.content\n                    self._emit(\n                        session_id,\n                        EventType.TASK_FAILED,\n                        {\"reason\": final_message},\n                    )\n                    return RunResult(\n                        session_id=session_id,\n                        success=False,\n                        final_message=final_message,\n                    )\n                messages.append(Message.tool_text(tool_call.id, tool_result.content))\n\n        final_message = \"Agent reached the maximum turn limit.\"\n        self._emit(session_id, EventType.TASK_FAILED, {\"reason\": final_message})\n        return RunResult(\n            session_id=session_id,\n            success=False,\n            final_message=final_message,\n        )\n\n    def _execute_tool_call(\n        self,\n        session_id: str,\n        tool_call: ToolCall,\n        workspace: Path,\n    ) -> ToolResult:\n        self._emit(\n            session_id,\n            EventType.TOOL_REQUESTED,\n            {\"tool\": tool_call.name, \"arguments\": tool_call.arguments},\n        )\n        command = tool_call.arguments.get(\"command\")\n        self._emit(session_id, EventType.PERMISSION_REQUESTED, {\"tool\": tool_call.name})\n        decision = self._permissions.evaluate_tool(\n            tool_call.name,\n            command=command if isinstance(command, str) else None,\n        )\n        if decision.outcome == \"ask\":\n            decision = self._resolve_ask_permission(\n                decision,\n                tool_call,\n                command=command if isinstance(command, str) else None,\n            )\n        self._emit(\n            session_id,\n            EventType.PERMISSION_RESOLVED,\n            {\"outcome\": decision.outcome, \"reason\": decision.reason},\n        )\n        if decision.outcome != \"allow\":\n            return ToolResult(\n                tool_call_id=tool_call.id,\n                content=f\"Tool {tool_call.name} denied: {decision.reason}\",\n                is_error=True,\n            )\n\n        tool = self._tools.get(tool_call.name)\n        tool_result = tool.run(\n            tool_call.arguments,\n            ToolContext(workspace=workspace, tool_call_id=tool_call.id),\n        )\n        self._emit(\n            session_id,\n            EventType.TOOL_COMPLETED,\n            {\n                \"tool\": tool_call.name,\n                \"is_error\": tool_result.is_error,\n                \"content\": tool_result.content,\n            },\n        )\n        return tool_result\n\n    def _resolve_ask_permission(\n        self,\n        decision: PermissionDecision,\n        tool_call: ToolCall,\n        command: str | None,\n    ) -> PermissionDecision:\n        if self._permissions.auto_approve:\n            return decision.model_copy(update={\"outcome\": \"allow\"})\n\n        if self._permission_approver is None:\n            return PermissionDecision(\n                outcome=\"deny\",\n                reason=(\n                    f\"Approval required for tool {tool_call.name}, \"\n                    \"but no permission approver is configured.\"\n                ),\n            )\n\n        resolved = self._permission_approver(\n            PermissionRequest(\n                tool_name=tool_call.name,\n                tool_call_id=tool_call.id,\n                arguments=tool_call.arguments,\n                reason=decision.reason,\n                command=command,\n            )\n        )\n        if resolved.outcome == \"ask\":\n            return PermissionDecision(\n                outcome=\"deny\",\n                reason=(\n                    f\"Approval unresolved for tool {tool_call.name}: \"\n                    f\"{resolved.reason}\"\n                ),\n            )\n        return resolved\n\n    def _emit(\n        self,\n        session_id: str,\n        event_type: EventType,\n        payload: dict[str, object],\n    ) -> None:\n        event = SessionEvent(session_id=session_id, type=event_type, payload=payload)\n        self._session_store.append(event)\n        for observer in self._observers:\n            observer.on_event(event)\n\n    def _collect_tool_calls(self, messages: list[Message]) -> list[ToolCall]:\n        calls: list[ToolCall] = []\n        for message in messages:\n            calls.extend(message.tool_calls())\n        return calls\n\n    def _final_text(self, messages: list[Message]) -> str:\n        for message in reversed(messages):\n            text = message.text()\n            if text:\n                return text\n        return \"\"\n\n    def _tool_specs(self) -> list[ToolSpec]:\n        return [\n            ToolSpec(\n                name=tool.name,\n                description=tool.description,\n                input_schema=tool.input_schema,\n            )\n            for tool in self._tools.list()\n        ]\n"
  },
  {
    "group": "runtime",
    "path": "src/citrus/runtime/events.py",
    "description": "结构化事件流模型，供 session store、observer、tracing 和未来 memory extraction 使用。",
    "symbols": [
      "EventType",
      "SessionEvent",
      "RuntimeObserver"
    ],
    "content": "from datetime import UTC, datetime\nfrom enum import StrEnum\nfrom typing import Any\n\nfrom pydantic import BaseModel, Field\n\n\nclass EventType(StrEnum):\n    TASK_STARTED = \"task_started\"\n    CONTEXT_BUILT = \"context_built\"\n    MODEL_REQUESTED = \"model_requested\"\n    MODEL_RESPONDED = \"model_responded\"\n    TOOL_REQUESTED = \"tool_requested\"\n    PERMISSION_REQUESTED = \"permission_requested\"\n    PERMISSION_RESOLVED = \"permission_resolved\"\n    TOOL_COMPLETED = \"tool_completed\"\n    TASK_COMPLETED = \"task_completed\"\n    TASK_FAILED = \"task_failed\"\n\n\nclass SessionEvent(BaseModel):\n    session_id: str\n    type: EventType\n    payload: dict[str, Any] = Field(default_factory=dict)\n    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))\n\n\nclass RuntimeObserver:\n    def on_event(self, event: SessionEvent) -> None:\n        return None\n\n"
  },
  {
    "group": "runtime",
    "path": "src/citrus/runtime/messages.py",
    "description": "runtime 内部统一消息模型，保留 tool_call_id 以支持 OpenAI-compatible tool result 回传。",
    "symbols": [
      "ToolCall",
      "TextBlock",
      "ToolCallBlock",
      "Message",
      "ToolResult",
      "ContentBlock"
    ],
    "content": "from typing import Any, Literal\n\nfrom pydantic import BaseModel\n\n\nclass ToolCall(BaseModel):\n    id: str\n    name: str\n    arguments: dict[str, Any]\n\n\nclass TextBlock(BaseModel):\n    type: Literal[\"text\"] = \"text\"\n    text: str\n\n\nclass ToolCallBlock(BaseModel):\n    type: Literal[\"tool_call\"] = \"tool_call\"\n    tool_call: ToolCall\n\n\nContentBlock = TextBlock | ToolCallBlock\n\n\nclass Message(BaseModel):\n    role: Literal[\"system\", \"user\", \"assistant\", \"tool\"]\n    content: list[ContentBlock]\n    tool_call_id: str | None = None\n\n    @classmethod\n    def user_text(cls, text: str) -> \"Message\":\n        return cls(role=\"user\", content=[TextBlock(text=text)])\n\n    @classmethod\n    def assistant_text(cls, text: str) -> \"Message\":\n        return cls(role=\"assistant\", content=[TextBlock(text=text)])\n\n    @classmethod\n    def assistant_tool_call(cls, tool_call: ToolCall) -> \"Message\":\n        return cls(role=\"assistant\", content=[ToolCallBlock(tool_call=tool_call)])\n\n    @classmethod\n    def tool_text(cls, tool_call_id: str, text: str) -> \"Message\":\n        return cls(\n            role=\"tool\",\n            content=[TextBlock(text=text)],\n            tool_call_id=tool_call_id,\n        )\n\n    def text(self) -> str:\n        return \"\\n\".join(\n            block.text for block in self.content if isinstance(block, TextBlock)\n        )\n\n    def tool_calls(self) -> list[ToolCall]:\n        return [\n            block.tool_call\n            for block in self.content\n            if isinstance(block, ToolCallBlock)\n        ]\n\n\nclass ToolResult(BaseModel):\n    tool_call_id: str = \"\"\n    content: str\n    is_error: bool = False\n"
  },
  {
    "group": "sessions",
    "path": "src/citrus/sessions/__init__.py",
    "description": "Session 子包入口，导出内存和 JSONL 事件存储。",
    "symbols": [],
    "content": "\"\"\"Session storage components.\"\"\"\n\n"
  },
  {
    "group": "sessions",
    "path": "src/citrus/sessions/base.py",
    "description": "SessionStore 协议，定义任务事件流如何创建 session 和追加事件。",
    "symbols": [
      "SessionStore"
    ],
    "content": "from typing import Protocol\n\nfrom citrus.runtime.events import SessionEvent\n\n\nclass SessionStore(Protocol):\n    def append(self, event: SessionEvent) -> None:\n        ...\n\n    def load(self, session_id: str) -> list[SessionEvent]:\n        ...\n\n"
  },
  {
    "group": "sessions",
    "path": "src/citrus/sessions/memory.py",
    "description": "内存 session store，适合 CLI V1 默认运行和单元测试。",
    "symbols": [
      "InMemorySessionStore"
    ],
    "content": "from collections import defaultdict\n\nfrom citrus.runtime.events import SessionEvent\n\n\nclass InMemorySessionStore:\n    def __init__(self) -> None:\n        self._events: dict[str, list[SessionEvent]] = defaultdict(list)\n\n    def append(self, event: SessionEvent) -> None:\n        self._events[event.session_id].append(event)\n\n    def load(self, session_id: str) -> list[SessionEvent]:\n        return list(self._events[session_id])\n\n"
  },
  {
    "group": "sessions",
    "path": "src/citrus/sessions/jsonl.py",
    "description": "JSONL session store，为可审计事件持久化和未来 replay 打基础。",
    "symbols": [
      "JsonlSessionStore"
    ],
    "content": "import json\nfrom pathlib import Path\n\nfrom citrus.runtime.events import SessionEvent\n\n\nclass JsonlSessionStore:\n    def __init__(self, directory: Path) -> None:\n        self._directory = directory\n        self._directory.mkdir(parents=True, exist_ok=True)\n\n    def append(self, event: SessionEvent) -> None:\n        path = self._path_for(event.session_id)\n        with path.open(\"a\", encoding=\"utf-8\") as file:\n            file.write(event.model_dump_json() + \"\\n\")\n\n    def load(self, session_id: str) -> list[SessionEvent]:\n        path = self._path_for(session_id)\n        if not path.exists():\n            return []\n        return [\n            SessionEvent.model_validate(json.loads(line))\n            for line in path.read_text(encoding=\"utf-8\").splitlines()\n            if line\n        ]\n\n    def _path_for(self, session_id: str) -> Path:\n        return self._directory / f\"{session_id}.jsonl\"\n\n"
  },
  {
    "group": "tools",
    "path": "src/citrus/tools/__init__.py",
    "description": "Tool 子包入口，导出工具协议、注册表、来源和本地工具。",
    "symbols": [],
    "content": "\"\"\"Tool contracts and registry.\"\"\"\n\n"
  },
  {
    "group": "tools",
    "path": "src/citrus/tools/base.py",
    "description": "工具端口定义，包含 ToolContext 和 Tool protocol。",
    "symbols": [
      "ToolContext",
      "Tool"
    ],
    "content": "from pathlib import Path\nfrom typing import Protocol\n\nfrom pydantic import BaseModel, Field\n\nfrom citrus.runtime.messages import ToolResult\n\n\nclass ToolContext(BaseModel):\n    workspace: Path = Field(default_factory=Path.cwd)\n    tool_call_id: str = \"\"\n\n\nclass Tool(Protocol):\n    name: str\n    description: str\n    input_schema: dict[str, object]\n\n    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:\n        ...\n"
  },
  {
    "group": "tools",
    "path": "src/citrus/tools/registry.py",
    "description": "工具注册表，将 tool spec 暴露给 provider，并按名称查找执行工具。",
    "symbols": [
      "ToolRegistry"
    ],
    "content": "from __future__ import annotations\n\nfrom collections.abc import Sequence\n\nfrom citrus.tools.base import Tool\nfrom citrus.tools.sources import ToolSource\n\n\nclass ToolRegistry:\n    def __init__(self) -> None:\n        self._tools: dict[str, Tool] = {}\n\n    def register(self, tool: Tool) -> None:\n        self._tools[tool.name] = tool\n\n    def get(self, name: str) -> Tool:\n        try:\n            return self._tools[name]\n        except KeyError as exc:\n            raise KeyError(f\"Unknown tool: {name}\") from exc\n\n    def list(self) -> list[Tool]:\n        return list(self._tools.values())\n\n    @classmethod\n    def from_sources(cls, sources: Sequence[ToolSource]) -> ToolRegistry:\n        registry = cls()\n        for source in sources:\n            for tool in source.list_tools():\n                registry.register(tool)\n        return registry\n\n    @classmethod\n    def with_default_local_tools(cls) -> ToolRegistry:\n        from citrus.tools.local import (\n            ReadFileTool,\n            RunShellTool,\n            SearchFilesTool,\n            WriteFileTool,\n        )\n\n        registry = cls()\n        tools: list[Tool] = [\n            ReadFileTool(),\n            WriteFileTool(),\n            SearchFilesTool(),\n            RunShellTool(),\n        ]\n        for tool in tools:\n            registry.register(tool)\n        return registry\n"
  },
  {
    "group": "tools",
    "path": "src/citrus/tools/sources.py",
    "description": "工具来源抽象，允许未来把本地、MCP 或远程工具统一加载进 registry。",
    "symbols": [
      "ToolSource",
      "StaticToolSource"
    ],
    "content": "from typing import Protocol\n\nfrom citrus.tools.base import Tool\n\n\nclass ToolSource(Protocol):\n    def list_tools(self) -> list[Tool]:\n        ...\n\n\nclass StaticToolSource:\n    def __init__(self, tools: list[Tool]) -> None:\n        self._tools = tools\n\n    def list_tools(self) -> list[Tool]:\n        return list(self._tools)\n\n"
  },
  {
    "group": "tools/local",
    "path": "src/citrus/tools/local/__init__.py",
    "description": "本地工具入口，导出文件、搜索和 shell 工具实现。",
    "symbols": [],
    "content": "\"\"\"Default local coding tools.\"\"\"\n\nfrom citrus.tools.local.read_file import ReadFileTool\nfrom citrus.tools.local.search import SearchFilesTool\nfrom citrus.tools.local.shell import RunShellTool\nfrom citrus.tools.local.write_file import WriteFileTool\n\n__all__ = [\"ReadFileTool\", \"RunShellTool\", \"SearchFilesTool\", \"WriteFileTool\"]\n\n"
  },
  {
    "group": "tools/local",
    "path": "src/citrus/tools/local/paths.py",
    "description": "workspace 路径解析工具，阻止工具访问工作区外路径。",
    "symbols": [
      "resolve_workspace_path"
    ],
    "content": "from pathlib import Path\n\n\ndef resolve_workspace_path(workspace: Path, path: str) -> Path:\n    root = workspace.resolve()\n    candidate = Path(path)\n    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()\n    if resolved != root and root not in resolved.parents:\n        raise ValueError(f\"Path is outside workspace: {path}\")\n    return resolved\n\n"
  },
  {
    "group": "tools/local",
    "path": "src/citrus/tools/local/read_file.py",
    "description": "读取 workspace 内文件的本地工具。",
    "symbols": [
      "ReadFileTool"
    ],
    "content": "from citrus.runtime.messages import ToolResult\nfrom citrus.tools.base import ToolContext\nfrom citrus.tools.local.paths import resolve_workspace_path\n\n\nclass ReadFileTool:\n    name = \"read_file\"\n    description = \"Read a text file inside the workspace.\"\n    input_schema: dict[str, object] = {\n        \"type\": \"object\",\n        \"properties\": {\"path\": {\"type\": \"string\"}},\n        \"required\": [\"path\"],\n    }\n\n    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:\n        try:\n            path = resolve_workspace_path(context.workspace, str(input[\"path\"]))\n            return ToolResult(\n                tool_call_id=context.tool_call_id,\n                content=path.read_text(encoding=\"utf-8\"),\n            )\n        except Exception as exc:\n            return ToolResult(\n                tool_call_id=context.tool_call_id,\n                content=str(exc),\n                is_error=True,\n            )\n"
  },
  {
    "group": "tools/local",
    "path": "src/citrus/tools/local/write_file.py",
    "description": "写入 workspace 内文件的本地工具，通常需要权限策略审批。",
    "symbols": [
      "WriteFileTool"
    ],
    "content": "from citrus.runtime.messages import ToolResult\nfrom citrus.tools.base import ToolContext\nfrom citrus.tools.local.paths import resolve_workspace_path\n\n\nclass WriteFileTool:\n    name = \"write_file\"\n    description = \"Write a text file inside the workspace.\"\n    input_schema: dict[str, object] = {\n        \"type\": \"object\",\n        \"properties\": {\n            \"path\": {\"type\": \"string\"},\n            \"content\": {\"type\": \"string\"},\n        },\n        \"required\": [\"path\", \"content\"],\n    }\n\n    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:\n        try:\n            path = resolve_workspace_path(context.workspace, str(input[\"path\"]))\n            path.parent.mkdir(parents=True, exist_ok=True)\n            path.write_text(str(input[\"content\"]), encoding=\"utf-8\")\n            return ToolResult(\n                tool_call_id=context.tool_call_id,\n                content=f\"Wrote {path.relative_to(context.workspace.resolve())}\",\n            )\n        except Exception as exc:\n            return ToolResult(\n                tool_call_id=context.tool_call_id,\n                content=str(exc),\n                is_error=True,\n            )\n"
  },
  {
    "group": "tools/local",
    "path": "src/citrus/tools/local/search.py",
    "description": "基于 ripgrep 的文本搜索工具，返回匹配行供模型继续推理。",
    "symbols": [
      "SearchFilesTool"
    ],
    "content": "from pathlib import Path\n\nfrom citrus.runtime.messages import ToolResult\nfrom citrus.tools.base import ToolContext\nfrom citrus.tools.local.paths import resolve_workspace_path\n\n\nclass SearchFilesTool:\n    name = \"search_files\"\n    description = \"Search workspace text files for a literal query.\"\n    input_schema: dict[str, object] = {\n        \"type\": \"object\",\n        \"properties\": {\n            \"query\": {\"type\": \"string\"},\n            \"path\": {\"type\": \"string\"},\n        },\n        \"required\": [\"query\"],\n    }\n\n    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:\n        try:\n            query = str(input[\"query\"])\n            root = resolve_workspace_path(\n                context.workspace,\n                str(input.get(\"path\", \".\")),\n            )\n            matches = self._search(root, context.workspace.resolve(), query)\n            return ToolResult(\n                tool_call_id=context.tool_call_id,\n                content=\"\\n\".join(matches),\n            )\n        except Exception as exc:\n            return ToolResult(\n                tool_call_id=context.tool_call_id,\n                content=str(exc),\n                is_error=True,\n            )\n\n    def _search(self, root: Path, workspace: Path, query: str) -> list[str]:\n        files = [root] if root.is_file() else sorted(path for path in root.rglob(\"*\"))\n        matches: list[str] = []\n        for path in files:\n            if not path.is_file() or any(part.startswith(\".\") for part in path.parts):\n                continue\n            try:\n                lines = path.read_text(encoding=\"utf-8\").splitlines()\n            except UnicodeDecodeError:\n                continue\n            for line_number, line in enumerate(lines, start=1):\n                if query in line:\n                    relative = path.relative_to(workspace)\n                    matches.append(f\"{relative}:{line_number}:{line}\")\n        return matches\n"
  },
  {
    "group": "tools/local",
    "path": "src/citrus/tools/local/shell.py",
    "description": "受 workspace 和权限策略约束的 shell 命令工具。",
    "symbols": [
      "RunShellTool"
    ],
    "content": "import subprocess\n\nfrom citrus.runtime.messages import ToolResult\nfrom citrus.tools.base import ToolContext\n\n\nclass RunShellTool:\n    name = \"run_shell\"\n    description = \"Run a shell command in the workspace.\"\n    input_schema: dict[str, object] = {\n        \"type\": \"object\",\n        \"properties\": {\"command\": {\"type\": \"string\"}},\n        \"required\": [\"command\"],\n    }\n\n    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:\n        command = str(input[\"command\"])\n        completed = subprocess.run(\n            command,\n            cwd=context.workspace,\n            shell=True,\n            check=False,\n            text=True,\n            capture_output=True,\n            timeout=30,\n        )\n        content = completed.stdout if completed.stdout else completed.stderr\n        return ToolResult(\n            tool_call_id=context.tool_call_id,\n            content=content,\n            is_error=completed.returncode != 0,\n        )\n"
  }
];
