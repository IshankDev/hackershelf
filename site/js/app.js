// HackerShelf - Main Application

// State
let books = [];
let mentions = [];
let stats = {};
let wantToReadList = JSON.parse(localStorage.getItem('hackershelf_want_to_read') || '[]');
let currentTheme = localStorage.getItem('hackershelf_theme') || 'light';

// Initialize
async function init() {
    // Set theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon();
    
    // Load data
    await loadData();
    
    // Setup routing
    setupRouting();
    
    // Setup theme toggle
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    
    // Handle initial route
    handleRoute();
    
    // Handle navigation
    window.addEventListener('hashchange', handleRoute);
}

async function loadData() {
    try {
        const [booksRes, mentionsRes, statsRes] = await Promise.all([
            fetch('./data/books.json'),
            fetch('./data/mentions.json'),
            fetch('./data/stats.json')
        ]);
        
        books = await booksRes.json();
        mentions = await mentionsRes.json();
        stats = await statsRes.json();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('app').innerHTML = '<div class="container"><div class="empty-state"><div class="empty-state-icon">⚠️</div><p>Error loading data. Please try again later.</p></div></div>';
    }
}

function setupRouting() {
    // Highlight active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
}

function handleRoute() {
    const hash = window.location.hash || '#/';
    const [_, route, param] = hash.split('/');
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const activeLink = document.querySelector(`.nav-link[href="#${route || '/'}"]`);
    if (activeLink) activeLink.classList.add('active');
    
    // Render appropriate page
    switch (route) {
        case '':
        case '#':
            renderHome();
            break;
        case 'browse':
            renderBrowse();
            break;
        case 'book':
            renderBookDetail(param);
            break;
        case 'list':
            renderWantToRead();
            break;
        case 'about':
            renderAbout();
            break;
        default:
            renderHome();
    }
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// Theme
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('hackershelf_theme', currentTheme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.querySelector('.theme-icon');
    icon.textContent = currentTheme === 'light' ? '🌙' : '☀️';
}

// Home Page
function renderHome() {
    const shuffled = [...books].sort(() => Math.random() - 0.5).slice(0, 24);
    
    const html = `
        <div class="hero">
            <h1 class="hero-title">HackerShelf</h1>
            <p class="hero-subtitle">The books Hacker News keeps telling each other to read</p>
            <div class="hero-stats">
                <div class="stat">
                    <span class="stat-number">${stats.book_count || 0}</span>
                    <span class="stat-label">Books</span>
                </div>
                <div class="stat">
                    <span class="stat-number">${stats.mention_count || 0}</span>
                    <span class="stat-label">Mentions</span>
                </div>
                <div class="stat">
                    <span class="stat-number">${stats.recommender_count || 0}</span>
                    <span class="stat-label">Recommenders</span>
                </div>
            </div>
        </div>
        
        <div class="books-grid">
            ${shuffled.map(book => renderBookCard(book)).join('')}
        </div>
        
        <div style="text-align: center;">
            <a href="#/browse" class="btn">Browse All Books →</a>
        </div>
    `;
    
    document.getElementById('app').innerHTML = `<div class="container">${html}</div>`;
}

// Browse Page
function renderBrowse() {
    const html = `
        <h1 style="margin-bottom: 24px;">Browse Books</h1>
        
        <div class="search-box">
            <input 
                type="text" 
                class="search-input" 
                id="searchInput" 
                placeholder="Search by title, author, or topic..."
            />
        </div>
        
        <div class="filters" id="filters">
            <div class="filter-group">
                <span class="filter-label">Kind:</span>
                <button class="filter-chip active" data-filter="kind" data-value="all">All</button>
                <button class="filter-chip" data-filter="kind" data-value="technical">Technical</button>
                <button class="filter-chip" data-filter="kind" data-value="business">Business</button>
                <button class="filter-chip" data-filter="kind" data-value="science">Science</button>
                <button class="filter-chip" data-filter="kind" data-value="fiction">Fiction</button>
            </div>
            <div class="filter-group">
                <span class="filter-label">Level:</span>
                <button class="filter-chip active" data-filter="level" data-value="all">All</button>
                <button class="filter-chip" data-filter="level" data-value="intro">Intro</button>
                <button class="filter-chip" data-filter="level" data-value="intermediate">Intermediate</button>
                <button class="filter-chip" data-filter="level" data-value="advanced">Advanced</button>
            </div>
        </div>
        
        <div id="browseResults">
            <div class="books-grid">
                ${books.map(book => renderBookCard(book)).join('')}
            </div>
        </div>
    `;
    
    document.getElementById('app').innerHTML = `<div class="container">${html}</div>`;
    
    // Setup search
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', () => filterBooks());
    
    // Setup filters
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            const filter = e.target.dataset.filter;
            // Toggle active state within filter group
            e.target.parentElement.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            e.target.classList.add('active');
            filterBooks();
        });
    });
}

function filterBooks() {
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const kindFilter = document.querySelector('.filter-chip[data-filter="kind"].active')?.dataset.value || 'all';
    const levelFilter = document.querySelector('.filter-chip[data-filter="level"].active')?.dataset.value || 'all';
    
    const filtered = books.filter(book => {
        // Search
        const searchMatch = !searchTerm || 
            book.title.toLowerCase().includes(searchTerm) ||
            book.author.toLowerCase().includes(searchTerm) ||
            book.topics?.some(t => t.toLowerCase().includes(searchTerm)) ||
            book.categories?.some(c => c.toLowerCase().includes(searchTerm));
        
        // Filters
        const kindMatch = kindFilter === 'all' || book.kind === kindFilter;
        const levelMatch = levelFilter === 'all' || book.level === levelFilter;
        
        return searchMatch && kindMatch && levelMatch;
    });
    
    const resultsHtml = filtered.length > 0 
        ? `<div class="books-grid">${filtered.map(book => renderBookCard(book)).join('')}</div>`
        : '<div class="empty-state"><div class="empty-state-icon">📚</div><p>No books found matching your criteria.</p></div>';
    
    document.getElementById('browseResults').innerHTML = resultsHtml;
}

// Book Card
function renderBookCard(book) {
    const coverUrl = book.cover_id 
        ? `https://covers.openlibrary.org/b/id/${book.cover_id}-M.jpg`
        : null;
    
    const coverHtml = coverUrl
        ? `<img src="${coverUrl}" alt="${book.title}" class="book-cover" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\\'book-cover-placeholder\\'><div class=\\'cover-title\\'>${escapeHtml(book.title)}</div><div class=\\'cover-author\\'>${escapeHtml(book.author)}</div></div>'"/>`
        : `<div class="book-cover-placeholder"><div class="cover-title">${escapeHtml(book.title)}</div><div class="cover-author">${escapeHtml(book.author)}</div></div>`;
    
    return `
        <a href="#/book/${book.work_key}" class="book-card">
            ${coverHtml}
            <div class="book-info">
                <div class="book-title">${escapeHtml(book.title)}</div>
                <div class="book-author">${escapeHtml(book.author)}</div>
                <div class="book-meta">
                    <span class="book-badge score">⭐ ${book.score}</span>
                    <span class="book-badge">${book.recommender_count} recs</span>
                </div>
            </div>
        </a>
    `;
}

// Book Detail Page
function renderBookDetail(workKey) {
    const book = books.find(b => b.work_key === workKey);
    if (!book) {
        document.getElementById('app').innerHTML = '<div class="container"><div class="empty-state"><div class="empty-state-icon">📚</div><p>Book not found.</p></div></div>';
        return;
    }
    
    const bookMentions = mentions.filter(m => m.work_key === workKey);
    const isInList = wantToReadList.includes(workKey);
    
    const coverUrl = book.cover_id 
        ? `https://covers.openlibrary.org/b/id/${book.cover_id}-L.jpg`
        : null;
    
    const coverHtml = coverUrl
        ? `<img src="${coverUrl}" alt="${book.title}" class="book-cover-large" onerror="this.parentElement.innerHTML='<div class=\\'book-cover-placeholder\\'style=\\'width:200px;aspect-ratio:2/3;border-radius:12px;\\'><div class=\\'cover-title\\'>${escapeHtml(book.title)}</div><div class=\\'cover-author\\'>${escapeHtml(book.author)}</div></div>'"/>`
        : `<div class="book-cover-placeholder" style="width:200px;aspect-ratio:2/3;border-radius:12px;"><div class="cover-title">${escapeHtml(book.title)}</div><div class="cover-author">${escapeHtml(book.author)}</div></div>`;
    
    const html = `
        <div class="book-detail">
            <div class="book-header">
                ${coverHtml}
                <div class="book-header-info">
                    <h1>${escapeHtml(book.title)}</h1>
                    <div class="author">${escapeHtml(book.author)}</div>
                    ${book.first_publish_year ? `<div style="color: var(--text-secondary); margin-bottom: 16px;">First published: ${book.first_publish_year}</div>` : ''}
                    <div class="book-categories">
                        ${book.categories?.map(c => `<span class="category-tag">${c}</span>`).join('') || ''}
                    </div>
                    <div class="book-actions">
                        <button class="btn ${isInList ? 'btn-secondary' : ''}" onclick="toggleWantToRead('${workKey}')">
                            ${isInList ? '✓ On Your List' : '+ Want to Read'}
                        </button>
                    </div>
                    <div style="margin-top: 20px;">
                        <span class="book-badge score">⭐ Score: ${book.score}</span>
                        <span class="book-badge">${book.recommender_count} recommenders</span>
                        <span class="book-badge">${book.mention_count} mentions</span>
                    </div>
                </div>
            </div>
            
            <div class="book-section">
                <h2>About This Book</h2>
                <p>${escapeHtml(book.summary || 'No summary available.')}</p>
            </div>
            
            <div class="book-section">
                <h2>Why HN Loves It</h2>
                <p>${escapeHtml(book.why_hn || 'Recommended by the Hacker News community.')}</p>
            </div>
            
            <div class="book-section">
                <h2>What HN Says</h2>
                <div class="mentions-list">
                    ${bookMentions.slice(0, 10).map(m => renderMention(m)).join('')}
                </div>
                ${bookMentions.length > 10 ? `<p style="text-align: center; margin-top: 20px; color: var(--text-secondary);">Showing 10 of ${bookMentions.length} mentions</p>` : ''}
            </div>
        </div>
    `;
    
    document.getElementById('app').innerHTML = `<div class="container">${html}</div>`;
}

function renderMention(mention) {
    const date = new Date(mention.time * 1000);
    const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const hnUrl = `https://news.ycombinator.com/item?id=${mention.comment_id}`;
    
    return `
        <div class="mention-card">
            <div class="mention-header">
                <div>
                    <a href="https://news.ycombinator.com/user?id=${mention.by}" class="mention-user" target="_blank">${mention.by}</a>
                    <span class="mention-date"> · ${dateStr}</span>
                </div>
                <span class="stance-badge stance-${mention.stance}">${mention.stance.replace('_', ' ')}</span>
            </div>
            ${mention.quote ? `<div class="mention-quote">"${escapeHtml(mention.quote)}"</div>` : ''}
            ${mention.why ? `<div class="mention-why">${escapeHtml(mention.why)}</div>` : ''}
            <a href="${hnUrl}" target="_blank" class="mention-link">View on Hacker News →</a>
        </div>
    `;
}

// Want to Read List
function toggleWantToRead(workKey) {
    const index = wantToReadList.indexOf(workKey);
    if (index === -1) {
        wantToReadList.push(workKey);
    } else {
        wantToReadList.splice(index, 1);
    }
    localStorage.setItem('hackershelf_want_to_read', JSON.stringify(wantToReadList));
    handleRoute(); // Refresh current page
}

function renderWantToRead() {
    const listBooks = books.filter(b => wantToReadList.includes(b.work_key));
    
    const html = `
        <h1 style="margin-bottom: 24px;">Want to Read</h1>
        ${listBooks.length > 0 
            ? `<div class="books-grid">${listBooks.map(book => renderBookCard(book)).join('')}</div>`
            : '<div class="empty-state"><div class="empty-state-icon">📚</div><p>Your reading list is empty. Browse books to add some!</p><a href="#/browse" class="btn" style="margin-top: 20px;">Browse Books</a></div>'
        }
    `;
    
    document.getElementById('app').innerHTML = `<div class="container">${html}</div>`;
}

// About Page
function renderAbout() {
    const html = `
        <div class="about-content">
            <h1>About HackerShelf</h1>
            
            <p>HackerShelf is a curated collection of books recommended by the Hacker News community, extracted from ${stats.year_range ? stats.year_range[0] + '-' + stats.year_range[1] : '2024-2026'} of HN comments.</p>
            
            <h2>Methodology</h2>
            <p>Following the approach pioneered by Andrej Karpathy's <a href="https://hackertube.org" target="_blank">HackerTube</a>, we:</p>
            <ul>
                <li>Scanned 9.4M Hacker News comments from January 2024 to August 2026</li>
                <li>Prefiltered to 11,519 strong candidates with book links or recommendation phrases</li>
                <li>Used Gemini 3.5 Flash Lite to extract book titles, authors, and stance</li>
                <li>Resolved books via Open Library API</li>
                <li>Applied filters: kept books with ≥3 recommenders in ≥3 different months</li>
                <li>Generated summaries and categorization via LLM</li>
            </ul>
            
            <h2>Scoring</h2>
            <p>Books are scored as: <code>Score = (distinct recommenders) + 2 × (strong recommendations)</code></p>
            
            <h2>Data &amp; Credits</h2>
            <p><strong>Source data:</strong> <a href="https://huggingface.co/datasets/open-index/hacker-news" target="_blank">open-index/hacker-news</a> dataset (ODC-By 1.0)</p>
            <p><strong>Book metadata:</strong> <a href="https://openlibrary.org" target="_blank">Open Library</a></p>
            <p><strong>Inspiration:</strong> <a href="https://hackertube.org" target="_blank">HackerTube</a> by Andrej Karpathy</p>
            <p><strong>License:</strong> This dataset is released under ODC-By 1.0. HN comments remain the work of their respective authors.</p>
            
            <h2>Download Data</h2>
            <p>The complete dataset is available for download:</p>
            <p><a href="./download/hackershelf-data.zip" class="btn">Download hackershelf-data.zip</a></p>
            
            <h2>Stats</h2>
            <ul>
                <li><strong>${stats.book_count || 0}</strong> books</li>
                <li><strong>${stats.mention_count || 0}</strong> mentions</li>
                <li><strong>${stats.recommender_count || 0}</strong> unique recommenders</li>
                <li>Time span: <strong>${stats.year_range ? stats.year_range[0] + '-' + stats.year_range[1] : 'N/A'}</strong></li>
            </ul>
            
        </div>
    `;
    
    document.getElementById('app').innerHTML = `<div class="container">${html}</div>`;
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start the app
init();
