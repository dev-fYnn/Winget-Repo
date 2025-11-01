function retrieve_url(input_id, display_id) {
    const preview = document.getElementById(display_id);
    const text = document.getElementById(input_id).value;
    const urlRegex = /(https?:\/\/[^\s]+|www\.[^\s]+)/gi;
    const matches = text.match(urlRegex);

    if (matches) {
        const links = matches.map(url => {
            let link = url;
            if (!link.startsWith('http://') && !link.startsWith('https://')) {
                link = 'https://' + link;
            }
            return `<a href="${link}" target="_blank">${url}</a>`;
        }).join(' • ');
        preview.innerHTML = `🔗 ${links}`;
    } else {
        preview.innerHTML = '';
    }
}