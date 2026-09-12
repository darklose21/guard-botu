import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# Render'ın uyutmaması için mini web sunucusu
app = Flask('')

@app.route('/')
def home():
    return "Guard Bot aktif ve çalışıyor!"

# Bot Ayarları
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True  # Komutların çalışması için gerekli
intents.moderation = True # Sunucu güncelleme ve ban yetkileri için gerekli

bot = commands.Bot(command_prefix="!", intents=intents)

# Güvenli Liste (Whitelist) - Kullanıcı ID'lerini buraya ekleyebilirsin
guvenli_liste = set()

@bot.event
async def on_ready():
    print(f"{bot.user.name} Guard sistemi aktif ve devriyede!")

# Güvenli Listeye Ekleme Komutu (Sadece sunucu sahibi kullanabilir)
@bot.command(name="ekle")
async def ekle(ctx, member: discord.Member):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Bu komutu sadece **Sunucu Sahibi** kullanabilir!", delete_after=5)
        return

    guvenli_liste.add(member.id)
    await ctx.send(f"✅ {member.mention} başarıyla güvenli listeye eklendi. Guard artık ona dokunmayacak.")

# Güvenli Listeden Çıkarma Komutu (Sadece sunucu sahibi kullanabilir)
@bot.command(name="çıkar")
async def çıkar(ctx, member: discord.Member):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Bu komutu sadece **Sunucu Sahibi** kullanabilir!", delete_after=5)
        return

    if member.id in guvenli_liste:
        guvenli_liste.remove(member.id)
        await ctx.send(f"❌ {member.mention} güvenli listeden çıkarıldı.")
    else:
        await ctx.send(f"⚠️ {member.mention} zaten güvenli listede değil.")

# Güvenli Listeyi Görme Komutu
@bot.command(name="güvenliliste")
async def guvenliliste(ctx):
    if ctx.author.id != ctx.guild.owner_id:
        return
    
    if not guvenli_liste:
        await ctx.send("Güvenli listede henüz kimse yok.")
        return

    liste_str = ", ".join([f"<@{uid}>" for uid in guvenli_liste])
    await ctx.send(f"🛡️ **Güvenli Liste Üyeleri:** {liste_str}")

# Sunucu Güncellendiğinde (Vanity URL / Özel Davet Değişimi Kontrolü)
@bot.event
async def on_guild_update(before: discord.Guild, after: discord.Guild):
    # Eğer eski vanity URL ile yeni vanity URL aynı değilse (Değiştirildiyse)
    if before.vanity_url_code != after.vanity_url_code:
        # Son günlüğü (audit log) inceleyerek bunu kimin yaptığını buluyoruz
        async for entry in after.audit_logs(limit=3, action=discord.AuditLogAction.guild_update):
            user = entry.user
            
            # Sunucu sahibiyse veya botun kendisiyse veya güvenli listedeyse dokunma
            if user.id == after.owner_id or user.id == bot.user.id or user.id in guvenli_liste:
                return
            
            # Güvenli listede değilse ve sahibi değilse ANINDA BANLA!
            try:
                await after.ban(user, reason="Guard: Yetkisiz özel davet (vanity URL) değişimi!")
                print(f"🚨 TEHLİKE! {user} sunucu davetini değiştirdiği için banlandı!")
            except Exception as e:
                print(f"Banlama sırasında hata oluştu: {e}")

# Web sunucusunu ve botu çakışmadan aynı anda çalıştıran kısım
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    def run_flask():
        app.run(host='0.0.0.0', port=port)
        
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    bot.run(os.getenv("BOT_TOKEN"))
