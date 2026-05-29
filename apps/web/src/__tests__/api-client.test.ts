describe('api client configuration', () => {
  const originalConsoleLog = console.log;
  const originalConsoleError = console.error;

  beforeEach(() => {
    jest.resetModules();
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com/';
    localStorage.clear();
    console.log = jest.fn();
    console.error = jest.fn();
  });

  afterEach(() => {
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
  });

  it('API client uses environment variable and trims trailing slashes', async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      text: async () => JSON.stringify({ tools: [] }),
    } as Response);
    global.fetch = fetchMock as unknown as typeof fetch;

    const { api } = await import('@/lib/api');
    await api.getTools();

    expect(fetchMock).toHaveBeenCalledWith('https://api.example.com/tools', expect.any(Object));
  });

  it('returns health debug details for the configured API', async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      text: async () => JSON.stringify({ status: 'ok' }),
    } as Response);
    global.fetch = fetchMock as unknown as typeof fetch;

    const { api } = await import('@/lib/api');
    const result = await api.getHealthDebug();

    expect(result).toEqual(
      expect.objectContaining({
        configuredApiUrl: 'https://api.example.com',
        requestUrl: 'https://api.example.com/health',
        status: 200,
        statusText: 'OK',
        data: { status: 'ok' },
        error: null,
      }),
    );
  });

  it('returns a clearer network error when the API is unreachable', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('Failed to fetch')) as unknown as typeof fetch;

    const { api } = await import('@/lib/api');

    await expect(api.getTools()).rejects.toThrow(
      'Unable to reach API at https://api.example.com/tools. Check NEXT_PUBLIC_API_URL in Vercel and open /debug-api for more details.',
    );
  });

  it('maps login response fields into frontend token and user', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      text: async () =>
        JSON.stringify({
          access_token: 'test-token',
          token_type: 'bearer',
          user_id: 'user-1',
          workspace_id: 'workspace-1',
          email: 'demo@velaris.ai',
        }),
    } as Response) as unknown as typeof fetch;

    const { api } = await import('@/lib/api');
    const result = await api.login('demo@velaris.ai', 'demo123');

    expect(result).toEqual({
      token: 'test-token',
      user: {
        id: 'user-1',
        email: 'demo@velaris.ai',
        workspace_id: 'workspace-1',
        full_name: 'demo',
      },
    });
  });

  it('throws a clear parsing error when login response misses required user fields', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      text: async () =>
        JSON.stringify({
          access_token: 'test-token',
          workspace_id: 'workspace-1',
        }),
    } as Response) as unknown as typeof fetch;

    const { api } = await import('@/lib/api');

    await expect(api.login('demo@velaris.ai', 'demo123')).rejects.toThrow(
      'Login response is missing required user fields',
    );
  });

  it('throws when login response does not include an access token', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      text: async () =>
        JSON.stringify({
          user_id: 'user-1',
          workspace_id: 'workspace-1',
          email: 'demo@velaris.ai',
        }),
    } as Response) as unknown as typeof fetch;

    const { api } = await import('@/lib/api');

    await expect(api.login('demo@velaris.ai', 'demo123')).rejects.toThrow(
      'Login response did not include an access token',
    );
  });
});
