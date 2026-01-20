/**
 * Cloudflare Worker - HuggingFace Image Generation Proxy
 *
 * Keeps API key server-side and adds CORS headers for PWA access.
 * Deploy: wrangler deploy
 * Set secret: wrangler secret put HUGGINGFACE_API_KEY
 */

// Stable Diffusion model on HuggingFace (free tier compatible)
const MODEL_ID = 'runwayml/stable-diffusion-v1-5';
const API_URL = `https://router.huggingface.co/models/${MODEL_ID}`;
const MAX_WORD_LENGTH = 50;
const API_TIMEOUT_MS = 30000; // 30 seconds for image generation

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
			const word = body?.word;

			// Strict input validation
			if (!word || typeof word !== 'string') {
				return new Response(JSON.stringify({ error: 'Word is required' }), {
					status: 400,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			const trimmedWord = word.trim().toLowerCase();
			if (trimmedWord.length === 0 || trimmedWord.length > MAX_WORD_LENGTH) {
				return new Response(JSON.stringify({ error: `Word must be 1-${MAX_WORD_LENGTH} characters` }), {
					status: 400,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			// Build the prompt for association image
			const prompt = buildPrompt(trimmedWord);

			// Call HuggingFace API with timeout
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

			let response;
			try {
				response = await fetch(API_URL, {
					method: 'POST',
					headers: {
						'Authorization': `Bearer ${env.HUGGINGFACE_API_KEY}`,
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({
						inputs: prompt,
						parameters: {
							negative_prompt: 'text, letters, words, writing, numbers, watermark, signature, logo, blurry, low quality',
							num_inference_steps: 25,
							guidance_scale: 7.5,
							width: 512,
							height: 512,
						},
						options: {
							wait_for_model: true,
						},
					}),
					signal: controller.signal,
				});
			} finally {
				clearTimeout(timeoutId);
			}

			// Handle model loading (503 response)
			if (response.status === 503) {
				const errorData = await response.json().catch(() => ({}));
				return new Response(JSON.stringify({
					error: 'Model is loading',
					estimated_time: errorData.estimated_time || 20,
					retry: true
				}), {
					status: 503,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			if (!response.ok) {
				console.error('HuggingFace API error:', response.status);
				const errorText = await response.text().catch(() => 'Unknown error');
				return new Response(JSON.stringify({ error: 'Image generation failed', details: errorText }), {
					status: 502,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			// Return image with CORS headers
			const imageBlob = await response.arrayBuffer();
			return new Response(imageBlob, {
				headers: {
					'Content-Type': 'image/png',
					'Cache-Control': 'public, max-age=31536000, immutable',
					...corsHeaders(),
				},
			});

		} catch (error) {
			if (error.name === 'AbortError') {
				return new Response(JSON.stringify({ error: 'Image generation timeout' }), {
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

/**
 * Build an optimized prompt for vocabulary association images
 */
function buildPrompt(word) {
	return `Surreal educational illustration to help remember the English word "${word}". Single main object related to the word. Placed in an unexpected but realistic situation. No text, no letters, no words. Clean background, soft pastel colors. High quality, detailed illustration style.`;
}

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
