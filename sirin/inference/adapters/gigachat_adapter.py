from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx
from loguru import logger as lg

from sirin.inference.adapters.openai_adapter import OpenAIModelAdapter


@dataclass
class GigaChatConfig:

    model_path: str = 'GigaChat-2-Max'
    base_url: Optional[str] = None

    # --- mTLS auth (client certificate) ---
    cert_file: Optional[str] = None
    key_file: Optional[str] = None

    # --- OAuth auth (bearer token; see fetch_oauth_token) ---
    api_key: Optional[str] = None
    credentials: Optional[str] = None
    scope: str = 'GIGACHAT_API_PERS'

    verify_ssl_certs: bool = False
    proxy_url: Optional[str] = None
    timeout: float = 600.0
    max_retries: int = 3

    device: Optional[str] = None
    extra_body: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        has_mtls = bool(self.cert_file and self.key_file)
        has_token = bool(self.api_key or self.credentials)
        if not (has_mtls or has_token):
            raise ValueError(
                'GigaChatConfig needs either cert_file+key_file (mTLS), api_key (a ready bearer '
                'token), or credentials (OAuth key to exchange for one).'
            )


class GigaChatModelAdapter(OpenAIModelAdapter):
    """GigaChat via SIRIN's OpenAI-compatible adapter.

    Only :meth:`load` differs from the parent: the HTTP clients carry the mTLS certificate and
    point at the GigaChat base URL. All inference methods are inherited.
    """

    def __init__(
        self,
        config: Optional[GigaChatConfig] = None,
        model: Any = None,
        tokenizer: Any = None,
    ):
        super().__init__(config, model, tokenizer)

    # ------------------------------------------------------------------ auth

    @staticmethod
    def fetch_oauth_token(credentials: str, scope: str = 'GIGACHAT_API_PERS') -> str:
        """Exchange an Authorization key for a bearer token via the ``gigachat`` SDK.

        CAVEAT: the returned token is valid for roughly 30 minutes and this adapter does NOT
        refresh it. A long evaluation run started near expiry will begin failing with 401s
        partway through. Prefer mTLS for anything longer than a few minutes, or re-create the
        adapter periodically.
        """
        try:
            from gigachat import GigaChat as GigaChatSDK
        except ImportError:
            raise ImportError(
                'OAuth mode needs the gigachat package: pip install gigachat. '
                '(mTLS mode does not require it.)'
            )
        with GigaChatSDK(credentials=credentials, scope=scope, verify_ssl_certs=False) as sdk:
            return sdk.get_token().access_token

    # ------------------------------------------------------------------ load

    def load(self, model: Any = None, tokenizer: Any = None):
        """Build OpenAI sync/async clients wired to GigaChat."""
        if self._is_loaded:
            lg.warning('GigaChat client already loaded')
            return

        if model is not None:
            self._client = model
            self._model_name = self.config.model_path
            self._is_loaded = True
            return

        # httpx takes the client certificate as a (cert, key) tuple.
        cert = None
        if self.config.cert_file and self.config.key_file:
            cert = (self.config.cert_file, self.config.key_file)

        # verify_ssl_certs=False disables MITM protection. GigaChat is signed by the Russian
        # Trusted Root CA, which is usually absent from the system trust store; installing that
        # CA and setting verify_ssl_certs=True is the correct production fix.
        verify = self.config.verify_ssl_certs
        if not verify:
            lg.warning(
                'verify_ssl_certs=False: TLS certificate validation is OFF. Install the '
                'Russian Trusted Root CA and enable it for production use.'
            )

        httpx_kwargs: Dict[str, Any] = {
            'timeout': self.config.timeout,
            'verify': verify,
        }
        if cert is not None:
            httpx_kwargs['cert'] = cert
        if self.config.proxy_url:
            httpx_kwargs['proxy'] = self.config.proxy_url

        api_key = self.config.api_key
        if api_key is None and self.config.credentials:
            lg.info('No api_key given; exchanging OAuth credentials for a bearer token.')
            api_key = self.fetch_oauth_token(self.config.credentials, self.config.scope)

        client_kwargs: Dict[str, Any] = {
            'timeout': self.config.timeout,
            # The OpenAI SDK refuses to start without some api_key. Under mTLS the certificate
            # is the real credential, so a placeholder is correct rather than a hack.
            'api_key': api_key or 'mtls-client-certificate',
        }
        if self.config.base_url:
            client_kwargs['base_url'] = self.config.base_url

        self._client = self.openai.OpenAI(
            http_client=httpx.Client(**httpx_kwargs), **client_kwargs
        )
        self._async_client = self.openai.AsyncOpenAI(
            http_client=httpx.AsyncClient(**httpx_kwargs), **client_kwargs
        )

        self._model_name = self.config.model_path
        self._is_loaded = True
        lg.info(f'Loaded GigaChat client for model: {self.config.model_path}')

    # -------------------------------------------------------------- utilities

    def list_models(self):
        """Model ids visible to these credentials -- a one-call connectivity check."""
        if not self._is_loaded:
            self.load()
        return [m.id for m in self._client.models.list().data]

    def probe_logprob_support(self) -> bool:
        """Ask the deployment once whether it returns token logprobs.

        Decides whether native logprob-scoring judges (``SequenceOpenAIJudge``) can be used, or
        whether you need a text-parsing judge. Run it once and cache the answer.
        """
        if not self._is_loaded:
            self.load()
        try:
            _, logprobs = self.sample(
                ['ping'], max_tokens=5, temperature=0.1, return_logprobs=True
            )
        except Exception as e:  # noqa: BLE001 - any failure means "unsupported"
            lg.info(f'logprobs unsupported ({type(e).__name__}: {e})')
            return False
        supported = bool(logprobs and logprobs[0])
        lg.info(f'logprobs supported: {supported}')
        return supported
