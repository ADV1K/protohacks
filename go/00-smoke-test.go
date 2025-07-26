package main

import (
	"adv1k/protohacks/netkit"
	"io"
)

func SmokeTest() {
	server := netkit.TCPServer{}
	server.RawHandler(
		func(conn netkit.Conn) {
			if _, err := io.Copy(conn, conn); err != nil {
				server.Logger.Error(err.Error())
			}
		})
	server.ListenAndServe()
}
