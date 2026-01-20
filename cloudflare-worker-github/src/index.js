/**
 * Cloudflare Worker - GitHub Image Commit Proxy
 *
 * Commits generated association images to GitHub repository.
 * Deploy: wrangler deploy
 * Set secret: wrangler secret put GITHUB_TOKEN
 */

const MAX_WORD_LENGTH = 50;

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
			const { word, imageBase64 } = body;

			// Validate word
			if (!word || typeof word !== 'string') {
				return new Response(JSON.stringify({ error: 'Word is required' }), {
					status: 400,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			const normalizedWord = word.trim().toLowerCase().replace(/[^a-z0-9-]/g, '_');
			if (normalizedWord.length === 0 || normalizedWord.length > MAX_WORD_LENGTH) {
				return new Response(JSON.stringify({ error: `Invalid word` }), {
					status: 400,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			// Validate image
			if (!imageBase64 || typeof imageBase64 !== 'string') {
				return new Response(JSON.stringify({ error: 'Image data is required' }), {
					status: 400,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			// File path in repo
			const filePath = `docs/images/${normalizedWord}.png`;

			// Check if file already exists
			const existingFile = await getFileFromGitHub(env, filePath);

			// Commit to GitHub
			const result = await commitToGitHub(env, filePath, imageBase64, existingFile?.sha);

			if (!result.success) {
				return new Response(JSON.stringify({ error: result.error }), {
					status: 502,
					headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
				});
			}

			// Return the raw GitHub URL
			const rawUrl = `https://raw.githubusercontent.com/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/${env.GITHUB_BRANCH}/${filePath}`;

			return new Response(JSON.stringify({
				success: true,
				url: rawUrl,
				path: filePath,
			}), {
				headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
			});

		} catch (error) {
			console.error('Worker error:', error);
			return new Response(JSON.stringify({ error: 'Internal server error' }), {
				status: 500,
				headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
			});
		}
	},
};

async function getFileFromGitHub(env, filePath) {
	try {
		const response = await fetch(
			`https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${filePath}?ref=${env.GITHUB_BRANCH}`,
			{
				headers: {
					'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
					'Accept': 'application/vnd.github.v3+json',
					'User-Agent': 'voca-github-proxy',
				},
			}
		);

		if (response.ok) {
			return await response.json();
		}
		return null;
	} catch {
		return null;
	}
}

async function commitToGitHub(env, filePath, contentBase64, existingSha) {
	try {
		const body = {
			message: `Add association image: ${filePath.split('/').pop()}`,
			content: contentBase64,
			branch: env.GITHUB_BRANCH,
		};

		// If file exists, include sha for update
		if (existingSha) {
			body.sha = existingSha;
			body.message = `Update association image: ${filePath.split('/').pop()}`;
		}

		const response = await fetch(
			`https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${filePath}`,
			{
				method: 'PUT',
				headers: {
					'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
					'Accept': 'application/vnd.github.v3+json',
					'Content-Type': 'application/json',
					'User-Agent': 'voca-github-proxy',
				},
				body: JSON.stringify(body),
			}
		);

		if (!response.ok) {
			const errorText = await response.text();
			console.error('GitHub API error:', response.status, errorText);
			return { success: false, error: `GitHub API error: ${response.status}` };
		}

		return { success: true };
	} catch (error) {
		console.error('GitHub commit error:', error);
		return { success: false, error: error.message };
	}
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
