sudo pip3 install -r requirements.txt
sudo cp agents_tyto.conf /etc/supervisor/conf.d/
sudo cp agents_tyto_nginx.conf /etc/nginx/sites-enabled/
sudo supervisorctl update
sudo systemctl restart nginx
sudo certbot --nginx -d tyto.ai.medsenger.ru
touch config.py
