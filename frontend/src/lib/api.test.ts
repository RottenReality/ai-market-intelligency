import { ApiError, apiFetch } from './api'

function respond(status: number, body: unknown, statusText = '') {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, statusText })))
}

afterEach(() => vi.unstubAllGlobals())

test('a plain string detail becomes the error text', async () => {
  respond(404, { detail: 'No AI analysis yet' })
  await expect(apiFetch('/x')).rejects.toEqual(new ApiError(404, 'No AI analysis yet'))
})

test('FastAPI validation errors show their messages, not the status text', async () => {
  respond(
    422,
    {
      detail: [
        { type: 'value_error', loc: ['body', 'channels'], msg: 'Value error, unknown channel: fax' },
        { type: 'string_too_long', loc: ['body', 'name'], msg: 'String should have at most 120 characters' },
      ],
    },
    'Unprocessable Content',
  )
  await expect(apiFetch('/x')).rejects.toMatchObject({
    status: 422,
    detail: 'unknown channel: fax. String should have at most 120 characters',
  })
})
