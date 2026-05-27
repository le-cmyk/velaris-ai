describe('api client configuration', () => {
  beforeEach(() => {
    jest.resetModules();
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com';
    localStorage.clear();
  });

  it('API client uses environment variable', async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ tools: [] }),
    } as Response);
    global.fetch = fetchMock as unknown as typeof fetch;

    const { api } = await import('@/lib/api');
    await api.getTools();

    expect(fetchMock).toHaveBeenCalledWith('https://api.example.com/tools', expect.any(Object));
  });
});
