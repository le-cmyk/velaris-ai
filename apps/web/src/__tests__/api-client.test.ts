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
});
