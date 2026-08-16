from radar.sources.forums import parse_feed
def test_parses_rss_and_atom():
    assert parse_feed('<rss><channel><item><guid>1</guid><title>T</title><description>manual work</description><link>https://x</link></item></channel></rss>', 'x')[0]['external_id'] == '1'
    assert parse_feed('<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>2</id><title>T</title><summary>too expensive</summary><link href="https://y"/></entry></feed>', 'x')[0]['url'] == 'https://y'
