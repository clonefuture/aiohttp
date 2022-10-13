import asyncio
import aiohttp


async def main():

    async with aiohttp.ClientSession() as session:

        response = await session.post('http://127.0.0.1:8080/users',
                                      json={'username': 'user_back',
                                            'password': '123456'}
                                      )
        print(response.status)
        print(await response.json())

        # response = await session.get('http://127.0.0.1:8080/users/2')
        # print(response.status)
        # print(await response.json())
        #
        # response = await session.patch('http://127.0.0.1:8080/users/5',
        #                                json={'username': 'user_new'})
        # print(response.status)
        # print(await response.json())

        # response = await session.get('http://127.0.0.1:8080/users/5')
        # print(response.status)
        # print(await response.json())

        # response = await session.delete('http://127.0.0.1:8080/users/1')
        # print(response.status)
        # print(await response.json())
        #
        # response = await session.get('http://127.0.0.1:8080/users/1')
        # print(response.status)
        # print(await response.json())


asyncio.run(main())
