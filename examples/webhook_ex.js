app.handle('rich_response', conv => {
    conv.add('This is a card rich response.');
    conv.add(new Card({
      title: 'Card Title',
      subtitle: 'Card Subtitle',
      text: 'Card Content',
      image: new Image({
        url: 'https://developers.google.com/assistant/assistant_96.png',
        alt: 'Google Assistant logo'
      })
    }));
  });