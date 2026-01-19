/**
 * Cloudflare Worker - ElevenLabs TTS Proxy
 *
 * Keeps API key server-side and adds CORS headers for PWA access.
 * Deploy: wrangler deploy
 * Set secret: wrangler secret put ELEVENLABS_API_KEY
 */

// Voice ID is fixed server-side for security (no client override)
const VOICE_ID = 'JBFqnCBsd6RMkjVDRZzb'; // George - English
const MODEL_ID = 'eleven_multilingual_v2';
const MAX_TEXT_LENGTH = 100; // Vocabulary words are short
const API_TIMEOUT_MS = 8000;

export default {
	async fetch(request, env) {
		// CORS preflight
		if (request.method === 'OPTIONS') {
			return handleCORS();
		}

		// Only allow POST
		if (request.method !== 'POST') {
			return new Response('Method not allowed', {
				status: 405,
				headers: corsHeaders(),
			});
		}

		// Validate Content-Type
		const contentType = request.headers.get('Content-Type');
		if (!contentType || !contentType.includes('application/json')) {
			return new Response(JSON.stringify({ error: 'Content-Type must be application/json' }), {
				status: 400,
				headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
			});
		}

		try {
			const body = await request.json();
			const text = body?.text;

			// Strict input validation
			if (!text || typeof text !== 'string') {
				return new Response(JSON.stringify({ error: 'Text is required' }), {
					status: 400,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			const trimmedText = text.trim();
			if (trimmedText.length === 0 || trimmedText.length > MAX_TEXT_LENGTH) {
				return new Response(JSON.stringify({ error: `Text must be 1-${MAX_TEXT_LENGTH} characters` }), {
					status: 400,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			// Call ElevenLabs API with timeout
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

			let response;
			try {
				response = await fetch(
					`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`,
					{
						method: 'POST',
						headers: {
							'Accept': 'audio/mpeg',
							'Content-Type': 'application/json',
							'xi-api-key': env.ELEVENLABS_API_KEY,
						},
						body: JSON.stringify({
							text: trimmedText,
							model_id: MODEL_ID,
							voice_settings: {
								stability: 0.5,
								similarity_boost: 0.75,
							},
						}),
						signal: controller.signal,
					}
				);
			} finally {
				clearTimeout(timeoutId);
			}

			if (!response.ok) {
				console.error('ElevenLabs API error:', response.status);
				return new Response(JSON.stringify({ error: 'TTS API failed' }), {
					status: 502,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			// Return audio with CORS and cache headers
			const audio = await response.arrayBuffer();
			return new Response(audio, {
				headers: {
					'Content-Type': 'audio/mpeg',
					'Cache-Control': 'public, max-age=31536000, immutable',
					...corsHeaders(),
				},
			});

		} catch (error) {
			if (error.name === 'AbortError') {
				return new Response(JSON.stringify({ error: 'TTS request timeout' }), {
					status: 504,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}
			console.error('Worker error:', error);
			return new Response(JSON.stringify({ error: 'Internal server error' }), {
				status: 500,
				headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
			});
		}
	},
};

function corsHeaders() {
	return {
		'Access-Control-Allow-Origin': '*',
		'Access-Control-Allow-Methods': 'POST, OPTIONS',
		'Access-Control-Allow-Headers': 'Content-Type',
	};
}

function handleCORS() {
	return new Response(null, {
		status: 204,
		headers: {
			...corsHeaders(),
			'Access-Control-Max-Age': '86400',
		},
	});
}
