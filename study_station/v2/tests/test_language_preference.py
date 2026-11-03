def test_offline_language_cookie_survives_navigation_to_live_membership(client):
    response = client.post('/api/v1/me', json={'lang': 'en'})
    assert response.status_code == 200
    client.cookies.set('ss_lang', 'hi')
    assert '<html lang="hi"' in client.get('/membership').text
    client.cookies.set('ss_lang', 'invalid-language')
    assert '<html lang="en"' in client.get('/membership').text
