_GITHUB_RIBBON_CSS = """
.github-ribbon {
    position: fixed;
    top: 40px;
    right: -65px;
    width: 230px;
    padding: 8px 0;
    background: #151513;
    color: #fff;
    text-align: center;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 13px;
    font-weight: bold;
    text-decoration: none;
    transform: rotate(45deg);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    border-top: 1px dashed rgba(255, 255, 255, 0.4);
    border-bottom: 1px dashed rgba(255, 255, 255, 0.4);
    z-index: 999;
}

.github-ribbon:hover {
    background: #333;
}
"""

_GITHUB_RIBBON_HTML = """        <a class="github-ribbon" href="https://github.com/nbr23/rss2podcast" target="_blank" rel="noopener noreferrer">
          Fork me on GitHub
        </a>
"""


def render_feed_style(show_github_ribbon: bool = True) -> str:
    ribbon_css = _GITHUB_RIBBON_CSS if show_github_ribbon else ""
    ribbon_html = _GITHUB_RIBBON_HTML if show_github_ribbon else ""
    return _FEED_STYLE_TMPL.replace("{{GITHUB_RIBBON_CSS}}", ribbon_css).replace(
        "{{GITHUB_RIBBON_HTML}}", ribbon_html
    )


_FEED_STYLE_TMPL = """<?xml version="1.0"?>
<xsl:stylesheet
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
                version="1.0">
  <xsl:output method="html"/>
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en">
      <head>
        <title>
          <xsl:value-of select="/rss/channel/title"/> | rss2podcast
        </title>
        <style>
.podcast-banner {
    display: block;
    background-color: #ffc107;
    color: #000;
    text-align: center;
    padding: 5px;
    margin: 0;
    border-bottom: 2px solid #e0a800;
    border-radius: 0 0 10px 10px;
    font-style: italic;
    font-family: monospace, monospace;
    font-weight: bold;
    font-size: 0.8em;
    text-decoration: none;
}

.podcast-banner:hover {
    background-color: #e0a800;
}

body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    margin: 0;
}

.content {
    margin: 0;
    padding: 20px;
}

.podcast-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.podcast-thumbnail {
    width: 100px;
    height: 100px;
    object-fit: cover;
    margin-right: 20px;
    display: none;
}

.podcast-title {
    font-size: 2em;
    margin: 0;
    color: #333;

    a {
        font-size: 0.5em;
        margin-left: 10px;
        text-decoration: none;
    }
}

.item-list {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.item {
    display: flex;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: transform 0.2s;
}

.thumbnail {
    width: 150px;
    height: 150px;
    object-fit: cover;
    border-right: 1px solid #ddd;
}

.item:hover {
    transform: scale(1.02);
}

.details {
    padding: 20px;
    flex: 1;
    color: inherit;
}

.title-link {
    text-decoration: none;
    color: inherit;
}

.title {
    font-size: 1.7em;
    margin: 0 0 10px;
    color: #333;
    font-weight: bold;
}

.description {
    font-size: 1em;
    margin: 0;
    color: #666;
}

.player {
    display: flex;
    justify-content: center;
    margin: 10px 0;
}

.player audio {
    width: 100%;
    height: auto;
}

{{GITHUB_RIBBON_CSS}}
        </style>
      </head>
      <body>
{{GITHUB_RIBBON_HTML}}        <a class="podcast-banner" href="#" onclick="this.href='pcast://'+location.host+location.pathname+location.search;">
            This page is a Podcast Feed, click to add it to your podcast player!
        </a>
        <div class="content">
          <div class="podcast-header">
            <xsl:if test="/rss/channel/itunes:image/@href">
              <img class="podcast-thumbnail" style="display: block;">
                <xsl:attribute name="src">
                  <xsl:value-of select="/rss/channel/itunes:image/@href"/>
                </xsl:attribute>
              </img>
            </xsl:if>
            <h1 class="podcast-title">
              <xsl:value-of select="/rss/channel/title"/>
              <a target="_blank" rel="noopener noreferrer">
              <xsl:attribute name="href">
                <xsl:value-of select="/rss/channel/link"/>
              </xsl:attribute>
              &#x1F517;
              </a>
            </h1>
          </div>
          <div class="item-list">
            <xsl:for-each select="/rss/channel/item">
            <div class="item">
              <xsl:if test="itunes:image/@href">
                <img class="thumbnail">
                  <xsl:attribute name="src">
                    <xsl:value-of select="itunes:image/@href"/>
                  </xsl:attribute>
                </img>
              </xsl:if>
              <div class="details">
                <a class="title-link" target="_blank" rel="noopener noreferrer">
                  <xsl:attribute name="href">
                    <xsl:value-of select="link"/>
                  </xsl:attribute>
                  <h3 class="title"><xsl:value-of select="title"/></h3>
                </a>
                <p class="player">
                  <audio controls="controls" preload="metadata">
                    <source>
                      <xsl:attribute name="src">
                        <xsl:value-of select="enclosure/@url"/>
                      </xsl:attribute>
                      <xsl:attribute name="type">
                        <xsl:value-of select="enclosure/@type"/>
                      </xsl:attribute>
                    </source>
                  </audio>
                </p>
                <div class="description">
                  <xsl:value-of select="description"/>
                </div>
              </div>
            </div>
            </xsl:for-each>
          </div>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
"""
