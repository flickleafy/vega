import React from 'react';
import { Button } from '../Button';
import { Container, Image, Text } from './styles';
import logo from '../../../assets/images/reactjs-icon.svg';

export function Greetings() {
  function handleSayHello() {
    window.electron.ipcRenderer.sendMessage('message', ['Hello World']);

    console.log('Message sent! Check main process log in terminal.');

    window.electron.ipcRenderer.on('message', (args) => {
      console.log('return', args);
    });
  }

  return (
    <Container>
      <Image
        src={logo}
        alt='ReactJS logo'
      />
      <Text>
        An Electron boilerplate including TypeScript, React, Jest and ESLint.
      </Text>
      <Button onClick={handleSayHello}>Send message to main process</Button>
    </Container>
  );
}
