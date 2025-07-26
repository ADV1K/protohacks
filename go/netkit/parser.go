package netkit

import (
	"bufio"
	"reflect"
)

func ReadLine[T any]() Parser {
	var zero T
	typ := reflect.TypeOf(zero)
	return func(conn Conn) <-chan ParsedMessage {
		out := make(chan ParsedMessage)
		go func() {
			defer close(out)
			scanner := bufio.NewScanner(conn)
			for scanner.Scan() {
				out <- ParsedMessage{
					Data: scanner.Bytes(),
					Type: typ,
				}
			}
		}()
		return out
	}
}

func LineEncoder(encoder Encoder) Encoder {
	return func(res any) ([]byte, error) {
		data, err := encoder(res)
		if err != nil {
			return []byte{}, err
		}
		return append(data, '\n'), nil
	}
}
